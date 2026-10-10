#!/usr/bin/env python3
"""Minimal local MQTT broker for the industrial control demo.

It supports the subset used by this project:
CONNECT, DISCONNECT, SUBSCRIBE and QoS 0/1/2 PUBLISH (delivered to subscribers at QoS 0).
"""

import socket
import struct
import threading
import time
from loguru import logger


class MQTTRouter:
    def __init__(self, host="127.0.0.1", port=1883):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.clients = set()
        self.subscriptions = {}
        self.lock = threading.Lock()

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(20)
        self.server_socket.settimeout(1.0)
        logger.info(f"MQTT broker listening on {self.host}:{self.port}")

        try:
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                except socket.timeout:
                    continue
                except OSError:
                    if self.running:
                        raise
                    break

                client_socket.settimeout(30.0)
                with self.lock:
                    self.clients.add(client_socket)
                logger.info(f"MQTT client connected: {address}")

                thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True,
                )
                thread.start()
        except KeyboardInterrupt:
            logger.info("MQTT broker interrupted")
        finally:
            if self.running:
                self.stop()

    def stop(self):
        self.running = False
        with self.lock:
            clients = list(self.clients)
            self.clients.clear()
            self.subscriptions.clear()

        for client in clients:
            self._close_client(client)

        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError:
                pass
            self.server_socket = None
        logger.info("MQTT broker stopped")

    def _handle_client(self, client_socket, address):
        try:
            while self.running:
                packet_type, flags, payload = self._read_packet(client_socket)
                if packet_type is None:
                    break

                if packet_type == 1:  # CONNECT
                    # 按客户端声明的 keepalive 放宽读超时（规范为 1.5 倍），否则空闲客户端会被提前断开
                    keepalive = self._parse_keepalive(payload)
                    client_socket.settimeout(keepalive * 1.5 if keepalive else None)
                    client_socket.sendall(b"\x20\x02\x00\x00")
                elif packet_type == 3:  # PUBLISH
                    qos = (flags >> 1) & 0x03
                    topic, message, packet_id = self._parse_publish(payload, qos)
                    if qos == 1:
                        client_socket.sendall(b"\x40\x02" + struct.pack("!H", packet_id))  # PUBACK
                    elif qos == 2:
                        client_socket.sendall(b"\x50\x02" + struct.pack("!H", packet_id))  # PUBREC
                    if topic:
                        logger.debug(f"MQTT publish: {topic}")
                        self._broadcast(topic, message, exclude=None)
                elif packet_type == 8:  # SUBSCRIBE
                    packet_id, topics = self._parse_subscribe(payload)
                    with self.lock:
                        for topic in topics:
                            self.subscriptions.setdefault(topic, set()).add(client_socket)
                    response = b"\x90" + self._encode_remaining_length(2 + len(topics))
                    response += struct.pack("!H", packet_id)
                    response += bytes([0] * len(topics))
                    client_socket.sendall(response)
                elif packet_type == 6:  # PUBREL（QoS 2 第二步）
                    client_socket.sendall(b"\x70\x02" + payload[:2])  # PUBCOMP
                elif packet_type == 12:  # PINGREQ
                    client_socket.sendall(b"\xd0\x00")
                elif packet_type == 14:  # DISCONNECT
                    break
        except Exception as exc:
            logger.debug(f"MQTT client {address} disconnected: {exc}")
        finally:
            self._remove_client(client_socket)

    def _read_packet(self, client_socket):
        fixed = client_socket.recv(1)
        if not fixed:
            return None, None, None

        first = fixed[0]
        packet_type = first >> 4
        flags = first & 0x0F
        remaining = self._read_remaining_length(client_socket)
        payload = self._recv_exact(client_socket, remaining)
        return packet_type, flags, payload

    def _read_remaining_length(self, client_socket):
        multiplier = 1
        value = 0
        while True:
            encoded = client_socket.recv(1)
            if not encoded:
                raise ConnectionError("socket closed while reading remaining length")
            byte = encoded[0]
            value += (byte & 127) * multiplier
            if (byte & 128) == 0:
                return value
            multiplier *= 128

    def _recv_exact(self, client_socket, size):
        chunks = []
        remaining = size
        while remaining:
            chunk = client_socket.recv(remaining)
            if not chunk:
                raise ConnectionError("socket closed while reading payload")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def _parse_keepalive(self, payload):
        try:
            name_len = struct.unpack("!H", payload[:2])[0]
            pos = 2 + name_len + 2  # 协议名 + 协议级别 + 连接标志
            return struct.unpack("!H", payload[pos:pos + 2])[0]
        except struct.error:
            return 60

    def _parse_publish(self, payload, qos=0):
        """QoS 1/2 的报文在主题后有 2 字节报文标识，必须去掉，否则会混进消息内容"""
        if len(payload) < 2:
            return None, b"", 0
        topic_len = struct.unpack("!H", payload[:2])[0]
        topic_start = 2
        topic_end = topic_start + topic_len
        topic = payload[topic_start:topic_end].decode("utf-8", errors="replace")
        packet_id = 0
        if qos:
            packet_id = struct.unpack("!H", payload[topic_end:topic_end + 2])[0]
            topic_end += 2
        return topic, payload[topic_end:], packet_id

    def _parse_subscribe(self, payload):
        if len(payload) < 2:
            return 0, []
        packet_id = struct.unpack("!H", payload[:2])[0]
        pos = 2
        topics = []
        while pos + 2 <= len(payload):
            topic_len = struct.unpack("!H", payload[pos:pos + 2])[0]
            pos += 2
            topic = payload[pos:pos + topic_len].decode("utf-8", errors="replace")
            pos += topic_len
            if pos < len(payload):
                pos += 1  # requested QoS
            topics.append(topic)
        return packet_id, topics

    def _broadcast(self, topic, message, exclude=None):
        packet = self._build_publish(topic, message)
        with self.lock:
            targets = [
                client
                for pattern, clients in self.subscriptions.items()
                if self._topic_matches(pattern, topic)
                for client in clients
                if client is not exclude
            ]

        for client in set(targets):
            try:
                client.sendall(packet)
            except OSError:
                self._remove_client(client)

    def _build_publish(self, topic, message):
        topic_bytes = topic.encode("utf-8")
        variable_header = struct.pack("!H", len(topic_bytes)) + topic_bytes
        payload = variable_header + message
        return b"\x30" + self._encode_remaining_length(len(payload)) + payload

    def _encode_remaining_length(self, value):
        encoded = bytearray()
        while True:
            digit = value % 128
            value //= 128
            if value > 0:
                digit |= 128
            encoded.append(digit)
            if value == 0:
                return bytes(encoded)

    def _topic_matches(self, pattern, topic):
        pattern_parts = pattern.split("/")
        topic_parts = topic.split("/")
        for index, part in enumerate(pattern_parts):
            if part == "#":
                return True
            if index >= len(topic_parts):
                return False
            if part != "+" and part != topic_parts[index]:
                return False
        return len(pattern_parts) == len(topic_parts)

    def _remove_client(self, client_socket):
        with self.lock:
            self.clients.discard(client_socket)
            for clients in self.subscriptions.values():
                clients.discard(client_socket)
        self._close_client(client_socket)

    def _close_client(self, client_socket):
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            client_socket.close()
        except OSError:
            pass


if __name__ == "__main__":
    logger.add(
        "logs/mqtt_broker_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
    )

    broker = MQTTRouter()
    try:
        broker.start()
    except Exception as exc:
        logger.error(f"MQTT broker failed: {exc}")
        time.sleep(3)
        raise
