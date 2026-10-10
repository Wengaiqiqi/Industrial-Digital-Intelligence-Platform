import * as THREE from 'three';

export class ModelBuilder {
    constructor(scene) {
        this.scene = scene;
        this.materials = this.createMaterials();
    }

    // 创建常用材质
    createMaterials() {
        return {
            metal: new THREE.MeshStandardMaterial({ 
                color: 0x888888, 
                metalness: 0.8, 
                roughness: 0.3,
                envMapIntensity: 1.0
            }),
            plastic: new THREE.MeshStandardMaterial({ 
                color: 0x4a90e2, 
                metalness: 0.1, 
                roughness: 0.8 
            }),
            glass: new THREE.MeshPhysicalMaterial({ 
                color: 0xffffff, 
                metalness: 0, 
                roughness: 0.05, 
                transmission: 0.95, 
                transparent: true,
                thickness: 0.5,
                ior: 1.5
            }),
            rubber: new THREE.MeshStandardMaterial({ 
                color: 0x1a1a1a, 
                metalness: 0, 
                roughness: 0.95,
                bumpScale: 0.1
            }),
            ceramic: new THREE.MeshStandardMaterial({ 
                color: 0xf8f8f8, 
                metalness: 0, 
                roughness: 0.2,
                clearcoat: 0.3
            }),
            copper: new THREE.MeshStandardMaterial({ 
                color: 0xb87333, 
                metalness: 0.9, 
                roughness: 0.1,
                envMapIntensity: 1.2
            }),
            steel: new THREE.MeshStandardMaterial({ 
                color: 0x606060, 
                metalness: 0.9, 
                roughness: 0.25,
                envMapIntensity: 1.0
            }),
            warning: new THREE.MeshStandardMaterial({ 
                color: 0xff6600, 
                emissive: 0x221100,
                metalness: 0.2, 
                roughness: 0.7 
            }),
            danger: new THREE.MeshStandardMaterial({ 
                color: 0xff0000, 
                emissive: 0x220000,
                metalness: 0.1, 
                roughness: 0.8 
            }),
            chrome: new THREE.MeshStandardMaterial({
                color: 0xc0c0c0,
                metalness: 1.0,
                roughness: 0.05,
                envMapIntensity: 2.0
            }),
            paint: new THREE.MeshStandardMaterial({
                color: 0x2196f3,
                metalness: 0.1,
                roughness: 0.4,
                clearcoat: 0.8
            })
        };
    }

    // 创建基础几何体
    createBox(width = 1, height = 1, depth = 1, material = 'metal') {
        const geometry = new THREE.BoxGeometry(width, height, depth);
        const mat = this.materials[material] || this.materials.metal;
        const mesh = new THREE.Mesh(geometry, mat.clone());
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        return mesh;
    }

    createCylinder(radiusTop = 1, radiusBottom = 1, height = 2, radialSegments = 32, material = 'metal') {
        const geometry = new THREE.CylinderGeometry(radiusTop, radiusBottom, height, radialSegments);
        const mat = this.materials[material] || this.materials.metal;
        const mesh = new THREE.Mesh(geometry, mat.clone());
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        return mesh;
    }

    createSphere(radius = 1, widthSegments = 32, heightSegments = 32, material = 'metal') {
        const geometry = new THREE.SphereGeometry(radius, widthSegments, heightSegments);
        const mat = this.materials[material] || this.materials.metal;
        const mesh = new THREE.Mesh(geometry, mat.clone());
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        return mesh;
    }

    createTorus(radius = 1, tube = 0.4, radialSegments = 16, tubularSegments = 32, material = 'metal') {
        const geometry = new THREE.TorusGeometry(radius, tube, radialSegments, tubularSegments);
        const mat = this.materials[material] || this.materials.metal;
        const mesh = new THREE.Mesh(geometry, mat.clone());
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        return mesh;
    }

    createCone(radius = 1, height = 2, radialSegments = 32, material = 'metal') {
        const geometry = new THREE.ConeGeometry(radius, height, radialSegments);
        const mat = this.materials[material] || this.materials.metal;
        const mesh = new THREE.Mesh(geometry, mat.clone());
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        return mesh;
    }

    // 创建管道
    createPipe(startPoint, endPoint, radius = 0.1, material = 'steel') {
        const direction = new THREE.Vector3().subVectors(endPoint, startPoint);
        const length = direction.length();
        
        const geometry = new THREE.CylinderGeometry(radius, radius, length, 16);
        const mat = this.materials[material] || this.materials.steel;
        const pipe = new THREE.Mesh(geometry, mat.clone());
        
        // 定位和旋转管道
        pipe.position.copy(startPoint).add(direction.multiplyScalar(0.5));
        pipe.lookAt(endPoint);
        pipe.rotateX(Math.PI / 2);
        
        pipe.castShadow = true;
        pipe.receiveShadow = true;
        
        return pipe;
    }

    // 创建复杂设备模型
    createPump(position = { x: 0, y: 0, z: 0 }, scale = 1) {
        const group = new THREE.Group();
        
        // 主泵体（更精细的形状）
        const body = this.createCylinder(1.2, 1.2, 1.6, 32, 'steel');
        body.position.set(0, 0.8, 0);
        
        // 蜗壳（螺旋形状近似）
        const spiralCasing = this.createTorus(1.4, 0.3, 16, 32, 'steel');
        spiralCasing.position.set(0, 0.8, 0);
        spiralCasing.rotation.x = Math.PI / 2;
        
        // 叶轮（内部可见）
        const impeller = this.createCylinder(0.6, 0.6, 0.2, 8, 'metal');
        impeller.position.set(0, 0.8, 0);
        
        // 叶轮叶片
        for (let i = 0; i < 6; i++) {
            const blade = this.createBox(0.1, 0.8, 0.15, 'metal');
            blade.position.set(
                0.4 * Math.cos(i * Math.PI / 3),
                0.8,
                0.4 * Math.sin(i * Math.PI / 3)
            );
            blade.rotation.y = i * Math.PI / 3;
            group.add(blade);
        }
        
        // 进口法兰（加强型）
        const inletFlange = this.createCylinder(0.9, 0.8, 0.15, 16, 'steel');
        inletFlange.rotation.z = Math.PI / 2;
        inletFlange.position.set(-1.5, 0.8, 0);
        
        // 出口法兰
        const outletFlange = this.createCylinder(0.7, 0.6, 0.15, 16, 'steel');
        outletFlange.rotation.x = Math.PI / 2;
        outletFlange.position.set(0, 0.8, 1.3);
        
        // 进口管道（带弯头）
        const inletPipe = this.createCylinder(0.35, 0.35, 1.2, 16, 'steel');
        inletPipe.rotation.z = Math.PI / 2;
        inletPipe.position.set(-2.1, 0.8, 0);
        
        // 出口管道（带弯头）
        const outletPipe = this.createCylinder(0.28, 0.28, 1.0, 16, 'steel');
        outletPipe.rotation.x = Math.PI / 2;
        outletPipe.position.set(0, 0.8, 1.8);
        
        // 电机（更详细）
        const motorBody = this.createCylinder(0.8, 0.8, 1.5, 16, 'metal');
        motorBody.position.set(0, 2.6, 0);
        
        // 电机接线盒
        const junctionBox = this.createBox(0.4, 0.3, 0.3, 'plastic');
        junctionBox.position.set(0.6, 2.6, 0);
        
        // 电机风扇罩（更精细）
        const fanCover = this.createCylinder(0.95, 0.95, 0.3, 24, 'metal');
        fanCover.position.set(0, 3.5, 0);
        
        // 风扇叶片
        for (let i = 0; i < 8; i++) {
            const fanBlade = this.createBox(0.05, 0.6, 0.15, 'metal');
            fanBlade.position.set(
                0.3 * Math.cos(i * Math.PI / 4),
                3.5,
                0.3 * Math.sin(i * Math.PI / 4)
            );
            fanBlade.rotation.y = i * Math.PI / 4 + Math.PI / 8;
            group.add(fanBlade);
        }
        
        // 联轴器
        const coupling = this.createCylinder(0.3, 0.3, 0.4, 16, 'steel');
        coupling.position.set(0, 1.9, 0);
        
        // 底座支撑（更稳固）
        const baseFrame = this.createBox(3, 0.2, 3, 'steel');
        baseFrame.position.set(0, 0.1, 0);
        
        const base1 = this.createBox(0.3, 1.6, 0.3, 'steel');
        base1.position.set(-1.2, 0.8, -1.2);
        
        const base2 = this.createBox(0.3, 1.6, 0.3, 'steel');
        base2.position.set(1.2, 0.8, -1.2);
        
        const base3 = this.createBox(0.3, 1.6, 0.3, 'steel');
        base3.position.set(-1.2, 0.8, 1.2);
        
        const base4 = this.createBox(0.3, 1.6, 0.3, 'steel');
        base4.position.set(1.2, 0.8, 1.2);
        
        // 压力表（更精细）
        const pressureGaugeBody = this.createCylinder(0.18, 0.18, 0.12, 16, 'plastic');
        pressureGaugeBody.position.set(0.8, 1.5, 0);
        
        const pressureGaugeFace = this.createCylinder(0.15, 0.15, 0.02, 16, 'ceramic');
        pressureGaugeFace.position.set(0.88, 1.5, 0);
        pressureGaugeFace.rotation.z = Math.PI / 2;
        
        // 控制阀（泄压）
        const reliefValve = this.createCylinder(0.1, 0.1, 0.3, 16, 'warning');
        reliefValve.position.set(-0.8, 1.5, 0);
        
        group.add(body, spiralCasing, impeller, inletFlange, outletFlange, 
                 inletPipe, outletPipe, motorBody, junctionBox, fanCover, 
                 coupling, baseFrame, base1, base2, base3, base4, 
                 pressureGaugeBody, pressureGaugeFace, reliefValve);
        
        group.position.set(position.x, position.y, position.z);
        group.scale.setScalar(scale);
        group.userData = { 
            type: 'pump', 
            deviceId: 'pump_' + Date.now(),
            rotatingParts: [impeller, motorBody, fanCover] // 可旋转部件
        };
        
        return group;
    }

    createTank(position = { x: 0, y: 0, z: 0 }, scale = 1) {
        const group = new THREE.Group();
        
        // 主罐体（更真实的比例）
        const tank = this.createCylinder(2.5, 2.5, 6, 32, 'steel');
        tank.position.set(0, 3, 0);
        
        // 罐顶（椭圆形封头）
        const tankTop = this.createSphere(2.5, 32, 16, 'steel');
        tankTop.scale.set(1, 0.4, 1);
        tankTop.position.set(0, 6.2, 0);
        
        // 罐底（平底）
        const tankBottom = this.createCylinder(2.5, 2.5, 0.2, 32, 'steel');
        tankBottom.position.set(0, 0.1, 0);
        
        // 支架腿（更稳固的设计）
        const supportHeight = 6;
        for (let i = 0; i < 8; i++) {
            const angle = (i * Math.PI * 2) / 8;
            const radius = 2.8;
            const x = radius * Math.cos(angle);
            const z = radius * Math.sin(angle);
            
            const support = this.createBox(0.25, supportHeight, 0.25, 'steel');
            support.position.set(x, supportHeight / 2, z);
            group.add(support);
            
            // 支撑梁
            if (i % 2 === 0) {
                const beam = this.createBox(0.2, 0.2, radius * 2, 'steel');
                beam.rotation.y = angle;
                beam.position.set(0, 1.5, 0);
                group.add(beam);
            }
        }
        
        // 支撑平台
        const platform = this.createCylinder(3.2, 3.2, 0.15, 32, 'steel');
        platform.position.set(0, 1.5, 0);
        
        // 人孔（带梯子）
        const manhole = this.createCylinder(0.5, 0.5, 0.25, 16, 'steel');
        manhole.position.set(2, 4, 0);
        manhole.rotation.z = Math.PI / 2;
        
        // 人孔盖
        const manholeCover = this.createCylinder(0.6, 0.6, 0.1, 16, 'steel');
        manholeCover.position.set(2.15, 4, 0);
        manholeCover.rotation.z = Math.PI / 2;
        
        // 梯子
        for (let i = 0; i < 15; i++) {
            const rung = this.createBox(0.05, 0.8, 0.05, 'steel');
            rung.position.set(2.7, 0.5 + i * 0.4, 0);
            group.add(rung);
        }
        
        // 梯子扶手
        const handrail1 = this.createBox(0.05, 0.05, 6, 'steel');
        handrail1.position.set(2.9, 3, -0.3);
        handrail1.rotation.x = Math.PI / 6;
        
        const handrail2 = this.createBox(0.05, 0.05, 6, 'steel');
        handrail2.position.set(2.9, 3, 0.3);
        handrail2.rotation.x = Math.PI / 6;
        
        // 液位计（玻璃管式）
        const levelGaugeHousing = this.createBox(0.15, 4, 0.4, 'steel');
        levelGaugeHousing.position.set(2.8, 3, 0);
        
        const levelGaugeGlass = this.createBox(0.08, 3.5, 0.15, 'glass');
        levelGaugeGlass.position.set(2.85, 3, 0);
        
        // 液位指示器刻度
        for (let i = 0; i < 8; i++) {
            const mark = this.createBox(0.05, 0.05, 0.1, 'warning');
            mark.position.set(2.95, 1.5 + i * 0.5, 0);
            group.add(mark);
        }
        
        // 液体（动态液位）
        const liquidLevel = this.createCylinder(2.4, 2.4, 4, 32, 'plastic');
        liquidLevel.material.color.setHex(0x4a90e2);
        liquidLevel.material.transparent = true;
        liquidLevel.material.opacity = 0.7;
        liquidLevel.position.set(0, 2, 0);
        liquidLevel.userData.isLevelIndicator = true;
        
        // 进料管（顶部）
        const inletPipe = this.createCylinder(0.2, 0.2, 1.5, 16, 'steel');
        inletPipe.position.set(-1.5, 7.5, 0);
        inletPipe.rotation.x = Math.PI / 6;
        
        // 进料阀门
        const inletValve = this.createBox(0.3, 0.3, 0.3, 'warning');
        inletValve.position.set(-1.5, 7, 0);
        
        // 出料管（底部）
        const outletPipe = this.createCylinder(0.25, 0.25, 1.5, 16, 'steel');
        outletPipe.position.set(0, 0.3, 3);
        outletPipe.rotation.x = Math.PI / 2;
        
        // 出料阀门
        const outletValve = this.createSphere(0.4, 16, 16, 'danger');
        outletValve.position.set(0, 0.3, 3.8);
        
        // 排气管
        const ventPipe = this.createCylinder(0.1, 0.1, 1.2, 16, 'steel');
        ventPipe.position.set(1.5, 7.5, 0);
        
        // 安全阀
        const safetyValve = this.createCone(0.15, 0.3, 16, 'danger');
        safetyValve.position.set(0, 6.8, 1.5);
        
        // 温度计
        const thermometer = this.createCylinder(0.05, 0.05, 0.8, 16, 'metal');
        thermometer.position.set(-2.2, 4, 0);
        thermometer.rotation.z = Math.PI / 4;
        
        // 压力表
        const pressureGauge = this.createCylinder(0.2, 0.2, 0.1, 16, 'plastic');
        pressureGauge.position.set(0, 6.5, 2.2);
        pressureGauge.rotation.x = -Math.PI / 4;
        
        group.add(tank, tankTop, tankBottom, platform, manhole, manholeCover,
                 handrail1, handrail2, levelGaugeHousing, levelGaugeGlass,
                 liquidLevel, inletPipe, inletValve, outletPipe, outletValve,
                 ventPipe, safetyValve, thermometer, pressureGauge);
        
        group.position.set(position.x, position.y, position.z);
        group.scale.setScalar(scale);
        group.userData = { 
            type: 'tank', 
            deviceId: 'tank_' + Date.now(),
            liquidLevel: liquidLevel,
            animatedParts: [liquidLevel] // 可动画部件
        };
        
        return group;
    }

    createHeatExchanger(position = { x: 0, y: 0, z: 0 }, scale = 1) {
        const group = new THREE.Group();
        
        // 主壳体
        const shell = this.createCylinder(1.5, 1.5, 6, 32, 'steel');
        shell.rotation.z = Math.PI / 2;
        shell.position.set(0, 1.5, 0);
        
        // 管束头部
        const headA = this.createCylinder(1.6, 1.6, 0.3, 32, 'steel');
        headA.rotation.z = Math.PI / 2;
        headA.position.set(-3.2, 1.5, 0);
        
        const headB = this.createCylinder(1.6, 1.6, 0.3, 32, 'steel');
        headB.rotation.z = Math.PI / 2;
        headB.position.set(3.2, 1.5, 0);
        
        // 进出口管嘴
        const inlet1 = this.createCylinder(0.3, 0.3, 0.8, 16, 'steel');
        inlet1.position.set(-1.5, 2.7, 0);
        
        const outlet1 = this.createCylinder(0.3, 0.3, 0.8, 16, 'steel');
        outlet1.position.set(1.5, 2.7, 0);
        
        const inlet2 = this.createCylinder(0.25, 0.25, 0.8, 16, 'copper');
        inlet2.position.set(-3.2, 2.7, 0);
        
        const outlet2 = this.createCylinder(0.25, 0.25, 0.8, 16, 'copper');
        outlet2.position.set(3.2, 2.7, 0);
        
        // 支撑架
        const support1 = this.createBox(0.2, 3, 0.2, 'steel');
        support1.position.set(-2, 0, -1);
        
        const support2 = this.createBox(0.2, 3, 0.2, 'steel');
        support2.position.set(2, 0, -1);
        
        const support3 = this.createBox(0.2, 3, 0.2, 'steel');
        support3.position.set(-2, 0, 1);
        
        const support4 = this.createBox(0.2, 3, 0.2, 'steel');
        support4.position.set(2, 0, 1);
        
        group.add(shell, headA, headB, inlet1, outlet1, inlet2, outlet2,
                 support1, support2, support3, support4);
        
        group.position.set(position.x, position.y, position.z);
        group.scale.setScalar(scale);
        group.userData = { 
            type: 'heat_exchanger', 
            deviceId: 'hx_' + Date.now()
        };
        
        return group;
    }

    createValve(position = { x: 0, y: 0, z: 0 }, scale = 1, valveType = 'gate') {
        const group = new THREE.Group();
        
        if (valveType === 'gate') {
            // 闸阀主体（更复杂的造型）
            const bodyLower = this.createBox(1.4, 1.2, 1.0, 'steel');
            bodyLower.position.set(0, 0.6, 0);
            
            const bodyUpper = this.createBox(0.8, 0.8, 0.8, 'steel');
            bodyUpper.position.set(0, 1.6, 0);
            
            // 阀盖（螺栓连接）
            const bonnet = this.createCylinder(0.5, 0.5, 0.4, 16, 'steel');
            bonnet.position.set(0, 2.2, 0);
            
            // 螺栓圈
            for (let i = 0; i < 8; i++) {
                const angle = (i * Math.PI * 2) / 8;
                const bolt = this.createCylinder(0.04, 0.04, 0.3, 8, 'steel');
                bolt.position.set(
                    0.6 * Math.cos(angle),
                    2.2,
                    0.6 * Math.sin(angle)
                );
                group.add(bolt);
            }
            
            // 阀杆
            const stem = this.createCylinder(0.12, 0.12, 2.0, 16, 'steel');
            stem.position.set(0, 2.8, 0);
            
            // 阀杆螺纹（装饰性）
            for (let i = 0; i < 15; i++) {
                const thread = this.createTorus(0.13, 0.02, 8, 16, 'steel');
                thread.position.set(0, 2.0 + i * 0.1, 0);
                group.add(thread);
            }
            
            // 手轮（更精细）
            const handwheelHub = this.createCylinder(0.3, 0.3, 0.2, 16, 'metal');
            handwheelHub.position.set(0, 3.9, 0);
            
            const handwheelRim = this.createTorus(0.7, 0.08, 16, 32, 'metal');
            handwheelRim.position.set(0, 3.9, 0);
            
            // 手轮辐条
            for (let i = 0; i < 6; i++) {
                const angle = (i * Math.PI * 2) / 6;
                const spoke = this.createBox(0.06, 0.6, 0.06, 'metal');
                spoke.rotation.z = angle;
                spoke.position.set(
                    0.35 * Math.cos(angle),
                    3.9,
                    0.35 * Math.sin(angle)
                );
                group.add(spoke);
            }
            
            // 法兰（加强版）
            const flange1 = this.createCylinder(0.8, 0.8, 0.2, 16, 'steel');
            flange1.rotation.z = Math.PI / 2;
            flange1.position.set(-0.8, 0.75, 0);
            
            const flange2 = this.createCylinder(0.8, 0.8, 0.2, 16, 'steel');
            flange2.rotation.z = Math.PI / 2;
            flange2.position.set(0.8, 0.75, 0);
            
            // 法兰螺栓
            for (let f = 0; f < 2; f++) {
                const flangeX = f === 0 ? -0.8 : 0.8;
                for (let i = 0; i < 8; i++) {
                    const angle = (i * Math.PI * 2) / 8;
                    const boltHead = this.createCylinder(0.05, 0.05, 0.08, 6, 'steel');
                    boltHead.rotation.z = Math.PI / 2;
                    boltHead.position.set(
                        flangeX,
                        0.75 + 0.6 * Math.cos(angle),
                        0.6 * Math.sin(angle)
                    );
                    group.add(boltHead);
                }
            }
            
            // 位置指示器
            const indicator = this.createBox(0.3, 0.6, 0.05, 'warning');
            indicator.position.set(0.5, 2.5, 0);
            
            group.add(bodyLower, bodyUpper, bonnet, stem, handwheelHub, 
                     handwheelRim, flange1, flange2, indicator);
            
        } else if (valveType === 'ball') {
            // 球阀主体（三段式设计）
            const bodyCenter = this.createSphere(1.0, 32, 32, 'steel');
            bodyCenter.position.set(0, 1.0, 0);
            
            const bodyLeft = this.createCylinder(0.7, 0.7, 0.6, 16, 'steel');
            bodyLeft.rotation.z = Math.PI / 2;
            bodyLeft.position.set(-0.8, 1.0, 0);
            
            const bodyRight = this.createCylinder(0.7, 0.7, 0.6, 16, 'steel');
            bodyRight.rotation.z = Math.PI / 2;
            bodyRight.position.set(0.8, 1.0, 0);
            
            // 球芯（内部可见）
            const ballCore = this.createSphere(0.7, 32, 32, 'metal');
            ballCore.position.set(0, 1.0, 0);
            ballCore.material.transparent = true;
            ballCore.material.opacity = 0.8;
            
            // 球芯通孔
            const ballHole = this.createCylinder(0.35, 0.35, 1.5, 16, 'rubber');
            ballHole.rotation.z = Math.PI / 2;
            ballHole.position.set(0, 1.0, 0);
            ballHole.material.color.setHex(0x222222);
            
            // 电动/气动执行器
            const actuatorBody = this.createBox(0.8, 1.2, 0.8, 'plastic');
            actuatorBody.position.set(0, 2.4, 0);
            
            // 执行器电机
            const actuatorMotor = this.createCylinder(0.3, 0.3, 0.6, 16, 'metal');
            actuatorMotor.position.set(0, 3.2, 0);
            
            // 位置反馈装置
            const feedback = this.createBox(0.4, 0.3, 0.2, 'plastic');
            feedback.position.set(0.5, 2.4, 0);
            
            // 指示灯
            const openLight = this.createSphere(0.08, 16, 16, 'plastic');
            openLight.material.color.setHex(0x00ff00);
            openLight.material.emissive.setHex(0x004400);
            openLight.position.set(-0.3, 3.2, 0.4);
            
            const closeLight = this.createSphere(0.08, 16, 16, 'danger');
            closeLight.material.emissive.setHex(0x440000);
            closeLight.position.set(0.3, 3.2, 0.4);
            
            // 法兰连接
            const flange1 = this.createCylinder(0.8, 0.8, 0.15, 16, 'steel');
            flange1.rotation.z = Math.PI / 2;
            flange1.position.set(-1.2, 1.0, 0);
            
            const flange2 = this.createCylinder(0.8, 0.8, 0.15, 16, 'steel');
            flange2.rotation.z = Math.PI / 2;
            flange2.position.set(1.2, 1.0, 0);
            
            // 阀杆密封
            const stemSeal = this.createCylinder(0.2, 0.2, 0.3, 16, 'rubber');
            stemSeal.position.set(0, 1.6, 0);
            
            // 控制电缆
            const cable = this.createCylinder(0.05, 0.05, 1.0, 8, 'rubber');
            cable.position.set(0.6, 3.5, 0);
            cable.rotation.x = Math.PI / 4;
            
            group.add(bodyCenter, bodyLeft, bodyRight, ballCore, ballHole,
                     actuatorBody, actuatorMotor, feedback, openLight, closeLight,
                     flange1, flange2, stemSeal, cable);
        }
        
        group.position.set(position.x, position.y, position.z);
        group.scale.setScalar(scale);
        group.userData = { 
            type: 'valve', 
            subtype: valveType,
            deviceId: `valve_${valveType}_${Date.now()}`,
            operatingParts: valveType === 'gate' ? ['stem'] : ['ballCore'] // 可操作部件
        };
        
        return group;
    }

    createConveyor(position = { x: 0, y: 0, z: 0 }, length = 10, scale = 1) {
        const group = new THREE.Group();
        
        // 传送带表面（带纹理效果）
        const belt = this.createBox(length, 0.12, 1.2, 'rubber');
        belt.position.set(0, 1.06, 0);
        
        // 传送带边缘挡板
        const sideGuard1 = this.createBox(length, 0.3, 0.05, 'steel');
        sideGuard1.position.set(0, 1.25, 0.62);
        
        const sideGuard2 = this.createBox(length, 0.3, 0.05, 'steel');
        sideGuard2.position.set(0, 1.25, -0.62);
        
        // 主框架结构
        const frame1 = this.createBox(length, 0.2, 0.2, 'steel');
        frame1.position.set(0, 0.5, -0.6);
        
        const frame2 = this.createBox(length, 0.2, 0.2, 'steel');
        frame2.position.set(0, 0.5, 0.6);
        
        // 横向支撑梁
        const numCrossBeams = Math.floor(length / 1.5) + 1;
        for (let i = 0; i < numCrossBeams; i++) {
            const x = -length/2 + (i * length / (numCrossBeams - 1));
            const crossBeam = this.createBox(0.15, 0.15, 1.4, 'steel');
            crossBeam.position.set(x, 0.5, 0);
            group.add(crossBeam);
        }
        
        // 支撑腿（更稳固的设计）
        const numSupports = Math.floor(length / 2) + 1;
        for (let i = 0; i < numSupports; i++) {
            const x = -length/2 + (i * length / (numSupports - 1));
            
            // 左侧支撑
            const leg1 = this.createBox(0.2, 1, 0.2, 'steel');
            leg1.position.set(x, 0, -0.6);
            
            const leg2 = this.createBox(0.2, 1, 0.2, 'steel');
            leg2.position.set(x, 0, 0.6);
            
            // 斜撑（增加稳定性）
            const brace1 = this.createBox(0.1, 0.05, 1.0, 'steel');
            brace1.rotation.x = Math.PI / 6;
            brace1.position.set(x, 0.3, 0);
            
            group.add(leg1, leg2, brace1);
            
            // 底座
            if (i % 2 === 0) {
                const base = this.createBox(0.6, 0.15, 1.6, 'steel');
                base.position.set(x, -0.075, 0);
                group.add(base);
            }
        }
        
        // 驱动滚筒（头部）
        const driveRoller = this.createCylinder(0.25, 0.25, 1.4, 24, 'steel');
        driveRoller.rotation.x = Math.PI / 2;
        driveRoller.position.set(length/2, 1, 0);
        
        // 从动滚筒（尾部）
        const tailRoller = this.createCylinder(0.25, 0.25, 1.4, 24, 'steel');
        tailRoller.rotation.x = Math.PI / 2;
        tailRoller.position.set(-length/2, 1, 0);
        
        // 托辊组（中间支撑滚筒）
        for (let i = 1; i < numSupports - 1; i++) {
            const x = -length/2 + (i * length / (numSupports - 1));
            
            // 中间托辊
            const idlerRoller = this.createCylinder(0.15, 0.15, 0.8, 16, 'steel');
            idlerRoller.rotation.x = Math.PI / 2;
            idlerRoller.position.set(x, 0.92, 0);
            
            // 侧托辊（V型结构）
            const sideRoller1 = this.createCylinder(0.1, 0.1, 0.4, 16, 'steel');
            sideRoller1.rotation.x = Math.PI / 2;
            sideRoller1.rotation.z = Math.PI / 6;
            sideRoller1.position.set(x, 0.85, 0.35);
            
            const sideRoller2 = this.createCylinder(0.1, 0.1, 0.4, 16, 'steel');
            sideRoller2.rotation.x = Math.PI / 2;
            sideRoller2.rotation.z = -Math.PI / 6;
            sideRoller2.position.set(x, 0.85, -0.35);
            
            group.add(idlerRoller, sideRoller1, sideRoller2);
        }
        
        // 驱动电机（更详细）
        const motorBase = this.createBox(1.0, 0.8, 0.8, 'steel');
        motorBase.position.set(length/2, 0.4, -1.5);
        
        const motor = this.createCylinder(0.4, 0.4, 0.8, 16, 'metal');
        motor.rotation.x = Math.PI / 2;
        motor.position.set(length/2, 0.8, -1.5);
        
        // 减速机
        const gearbox = this.createBox(0.6, 0.6, 0.6, 'metal');
        gearbox.position.set(length/2, 0.8, -0.9);
        
        // 联轴器
        const coupling = this.createCylinder(0.15, 0.15, 0.3, 16, 'warning');
        coupling.rotation.x = Math.PI / 2;
        coupling.position.set(length/2, 1, -0.6);
        
        // 传动链条/皮带保护罩
        const guardCover = this.createBox(1.2, 0.4, 0.3, 'plastic');
        guardCover.position.set(length/2, 1.2, -0.75);
        
        // 控制箱
        const controlBox = this.createBox(0.4, 0.6, 0.3, 'plastic');
        controlBox.position.set(length/2 - 1.5, 1.5, -0.8);
        
        // 急停按钮
        const emergencyStop = this.createCylinder(0.08, 0.08, 0.05, 16, 'danger');
        emergencyStop.position.set(length/2 - 1.5, 1.8, -0.65);
        
        // 载货（示例货物）
        for (let i = 0; i < Math.floor(length / 3); i++) {
            const cargoX = -length/2 + 1 + (i * 3);
            const cargo = this.createBox(0.8, 0.5, 0.6, 'warning');
            cargo.position.set(cargoX, 1.4, 0);
            group.add(cargo);
        }
        
        group.add(belt, sideGuard1, sideGuard2, frame1, frame2, 
                 driveRoller, tailRoller, motorBase, motor, gearbox, 
                 coupling, guardCover, controlBox, emergencyStop);
        
        group.position.set(position.x, position.y, position.z);
        group.scale.setScalar(scale);
        group.userData = { 
            type: 'conveyor', 
            deviceId: 'conveyor_' + Date.now(),
            movingParts: [belt, driveRoller, tailRoller], // 可移动部件
            rotatingParts: [motor] // 可旋转部件
        };
        
        return group;
    }

    // 创建复合工厂场景
    createFactory(position = { x: 0, y: 0, z: 0 }) {
        const group = new THREE.Group();
        
        // 主要设备布局
        const mainTank = this.createTank({ x: 0, y: 0, z: 0 }, 0.6);
        const pump1 = this.createPump({ x: 12, y: 0, z: 0 }, 0.5);
        const pump2 = this.createPump({ x: 12, y: 0, z: 8 }, 0.5);
        const heatExchanger = this.createHeatExchanger({ x: 0, y: 0, z: 15 }, 0.6);
        const storageConveyor = this.createConveyor({ x: -15, y: 0, z: 5 }, 6, 0.6);
        const productConveyor = this.createConveyor({ x: 8, y: 0, z: 15 }, 8, 0.6);
        
        // 辅助储罐
        const auxiliaryTank1 = this.createTank({ x: -12, y: 0, z: -8 }, 0.4);
        const auxiliaryTank2 = this.createTank({ x: -12, y: 0, z: 8 }, 0.4);
        
        // 阀门系统
        const valve1 = this.createValve({ x: 6, y: 0, z: 0 }, 0.8, 'ball');
        const valve2 = this.createValve({ x: 6, y: 0, z: 4 }, 0.8, 'gate');
        const valve3 = this.createValve({ x: 0, y: 0, z: 8 }, 0.8, 'ball');
        
        // 管道网络系统
        const pipes = [];
        
        // 主流程管道
        pipes.push(this.createPipe(
            new THREE.Vector3(2.4, 1.5, 0), 
            new THREE.Vector3(10, 1.5, 0), 
            0.15, 'steel'
        ));
        
        pipes.push(this.createPipe(
            new THREE.Vector3(14, 2.5, 0), 
            new THREE.Vector3(14, 2.5, 6), 
            0.12, 'steel'
        ));
        
        pipes.push(this.createPipe(
            new THREE.Vector3(14, 2.5, 6), 
            new THREE.Vector3(2, 2.5, 12), 
            0.12, 'copper'
        ));
        
        // 回流管道
        pipes.push(this.createPipe(
            new THREE.Vector3(-2, 2.5, 12), 
            new THREE.Vector3(-2, 2.5, 2), 
            0.1, 'steel'
        ));
        
        pipes.push(this.createPipe(
            new THREE.Vector3(-2, 2.5, 2), 
            new THREE.Vector3(-2, 3.5, 2), 
            0.1, 'steel'
        ));
        
        // 辅助管道连接
        pipes.push(this.createPipe(
            new THREE.Vector3(-10, 2, -8), 
            new THREE.Vector3(-2, 2, 0), 
            0.08, 'steel'
        ));
        
        pipes.push(this.createPipe(
            new THREE.Vector3(-10, 2, 8), 
            new THREE.Vector3(-2, 2, 0), 
            0.08, 'steel'
        ));
        
        // 控制室
        const controlRoom = this.createBox(6, 4, 4, 'paint');
        controlRoom.position.set(-8, 2, -15);
        
        // 控制室窗户
        const window1 = this.createBox(2, 1.5, 0.1, 'glass');
        window1.position.set(-5, 2.5, -13);
        
        const window2 = this.createBox(2, 1.5, 0.1, 'glass');
        window2.position.set(-11, 2.5, -13);
        
        // 控制室门
        const door = this.createBox(1, 2.5, 0.1, 'steel');
        door.position.set(-8, 1.25, -13);
        
        // 电气柜
        for (let i = 0; i < 3; i++) {
            const cabinet = this.createBox(1, 2.5, 0.6, 'metal');
            cabinet.position.set(-12 + i * 1.5, 1.25, -17);
            group.add(cabinet);
        }
        
        // 平台和楼梯
        const platform1 = this.createBox(8, 0.2, 4, 'steel');
        platform1.position.set(0, 4, 0);
        
        const platform2 = this.createBox(6, 0.2, 3, 'steel');
        platform2.position.set(12, 3, 0);
        
        // 楼梯
        for (let i = 0; i < 12; i++) {
            const step = this.createBox(2, 0.1, 0.3, 'steel');
            step.position.set(-4, 0.3 + i * 0.3, -2 + i * 0.2);
            group.add(step);
        }
        
        // 楼梯扶手
        const handrail = this.createBox(0.1, 0.1, 4, 'steel');
        handrail.position.set(-3, 2, -1);
        handrail.rotation.x = Math.PI / 6;
        
        // 安全设施
        const fireExtinguisher1 = this.createCylinder(0.15, 0.15, 0.8, 16, 'danger');
        fireExtinguisher1.position.set(-6, 0.4, -10);
        
        const fireExtinguisher2 = this.createCylinder(0.15, 0.15, 0.8, 16, 'danger');
        fireExtinguisher2.position.set(8, 0.4, 10);
        
        // 急停按钮
        const emergencyStop = this.createCylinder(0.2, 0.2, 0.1, 16, 'danger');
        emergencyStop.position.set(6, 1.5, -2);
        
        // 照明
        for (let i = 0; i < 4; i++) {
            for (let j = 0; j < 3; j++) {
                const light = this.createBox(1, 0.1, 0.5, 'plastic');
                light.position.set(-10 + i * 8, 8, -10 + j * 10);
                light.material.emissive.setHex(0x444444);
                group.add(light);
            }
        }
        
        // 组装所有组件
        group.add(mainTank, pump1, pump2, heatExchanger, storageConveyor, productConveyor);
        group.add(auxiliaryTank1, auxiliaryTank2);
        group.add(valve1, valve2, valve3);
        group.add(controlRoom, window1, window2, door);
        group.add(platform1, platform2, handrail);
        group.add(fireExtinguisher1, fireExtinguisher2, emergencyStop);
        
        // 添加所有管道
        pipes.forEach(pipe => group.add(pipe));
        
        group.position.set(position.x, position.y, position.z);
        group.userData = { 
            type: 'factory', 
            deviceId: 'factory_' + Date.now(),
            components: {
                tanks: [mainTank, auxiliaryTank1, auxiliaryTank2],
                pumps: [pump1, pump2],
                conveyors: [storageConveyor, productConveyor],
                valves: [valve1, valve2, valve3],
                heatExchanger: heatExchanger
            }
        };
        
        return group;
    }
}
