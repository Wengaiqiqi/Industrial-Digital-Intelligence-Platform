import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js';
import { MTLLoader } from 'three/examples/jsm/loaders/MTLLoader.js';
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js';

export class ModelLoader {
    constructor(scene) {
        this.scene = scene;
        this.gltfLoader = new GLTFLoader();
        this.objLoader = new OBJLoader();
        this.mtlLoader = new MTLLoader();
        this.fbxLoader = new FBXLoader();
        this.loadingManager = new THREE.LoadingManager();
        this.setupLoadingManager();
    }

    setupLoadingManager() {
        this.loadingManager.onStart = (url, itemsLoaded, itemsTotal) => {
            console.log('开始加载模型:', url);
        };

        this.loadingManager.onProgress = (url, itemsLoaded, itemsTotal) => {
            const progress = (itemsLoaded / itemsTotal * 100).toFixed(2);
            console.log('加载进度:', progress + '%');
        };

        this.loadingManager.onLoad = () => {
            console.log('模型加载完成');
        };

        this.loadingManager.onError = (url) => {
            console.error('模型加载失败:', url);
        };
    }

    // 加载GLTF/GLB模型
    async loadGLTF(url, position = { x: 0, y: 0, z: 0 }, scale = 1) {
        return new Promise((resolve, reject) => {
            this.gltfLoader.setLoadingManager(this.loadingManager);
            this.gltfLoader.load(
                url,
                (gltf) => {
                    const model = gltf.scene;
                    model.position.set(position.x, position.y, position.z);
                    model.scale.setScalar(scale);
                    
                    // 设置阴影
                    model.traverse((child) => {
                        if (child.isMesh) {
                            child.castShadow = true;
                            child.receiveShadow = true;
                            
                            // 确保材质正确设置
                            if (child.material) {
                                if (Array.isArray(child.material)) {
                                    child.material.forEach(mat => {
                                        mat.needsUpdate = true;
                                    });
                                } else {
                                    child.material.needsUpdate = true;
                                }
                            }
                        }
                    });
                    
                    this.scene.add(model);
                    
                    // 如果有动画，设置动画混合器
                    if (gltf.animations && gltf.animations.length > 0) {
                        const mixer = new THREE.AnimationMixer(model);
                        gltf.animations.forEach((clip) => {
                            mixer.clipAction(clip).play();
                        });
                        model.userData.mixer = mixer;
                    }
                    
                    resolve({
                        model: model,
                        animations: gltf.animations,
                        mixer: model.userData.mixer
                    });
                },
                (progress) => {
                    console.log('GLTF加载进度:', (progress.loaded / progress.total * 100) + '%');
                },
                (error) => {
                    console.error('GLTF加载失败:', error);
                    reject(error);
                }
            );
        });
    }

    // 加载OBJ模型
    async loadOBJ(objUrl, mtlUrl = null, position = { x: 0, y: 0, z: 0 }, scale = 1) {
        return new Promise((resolve, reject) => {
            if (mtlUrl) {
                this.mtlLoader.setLoadingManager(this.loadingManager);
                this.mtlLoader.load(mtlUrl, (materials) => {
                    materials.preload();
                    this.objLoader.setMaterials(materials);
                    this.loadOBJFile(objUrl, position, scale, resolve, reject);
                });
            } else {
                this.loadOBJFile(objUrl, position, scale, resolve, reject);
            }
        });
    }

    loadOBJFile(url, position, scale, resolve, reject) {
        this.objLoader.setLoadingManager(this.loadingManager);
        this.objLoader.load(
            url,
            (object) => {
                object.position.set(position.x, position.y, position.z);
                object.scale.setScalar(scale);
                
                // 设置阴影
                object.traverse((child) => {
                    if (child.isMesh) {
                        child.castShadow = true;
                        child.receiveShadow = true;
                    }
                });
                
                this.scene.add(object);
                resolve({ model: object });
            },
            (progress) => {
                console.log('OBJ加载进度:', (progress.loaded / progress.total * 100) + '%');
            },
            (error) => {
                console.error('OBJ加载失败:', error);
                reject(error);
            }
        );
    }

    // 加载FBX模型
    async loadFBX(url, position = { x: 0, y: 0, z: 0 }, scale = 1) {
        return new Promise((resolve, reject) => {
            this.fbxLoader.setLoadingManager(this.loadingManager);
            this.fbxLoader.load(
                url,
                (object) => {
                    object.position.set(position.x, position.y, position.z);
                    object.scale.setScalar(scale);
                    
                    // 设置阴影
                    object.traverse((child) => {
                        if (child.isMesh) {
                            child.castShadow = true;
                            child.receiveShadow = true;
                        }
                    });
                    
                    this.scene.add(object);
                    
                    // 如果有动画，设置动画混合器
                    if (object.animations && object.animations.length > 0) {
                        const mixer = new THREE.AnimationMixer(object);
                        object.animations.forEach((clip) => {
                            mixer.clipAction(clip).play();
                        });
                        object.userData.mixer = mixer;
                    }
                    
                    resolve({
                        model: object,
                        animations: object.animations,
                        mixer: object.userData.mixer
                    });
                },
                (progress) => {
                    console.log('FBX加载进度:', (progress.loaded / progress.total * 100) + '%');
                },
                (error) => {
                    console.error('FBX加载失败:', error);
                    reject(error);
                }
            );
        });
    }

    // 从文件加载模型
    async loadFromFile(file, position = { x: 0, y: 0, z: 0 }, scale = 1) {
        const url = URL.createObjectURL(file);
        const extension = file.name.split('.').pop().toLowerCase();
        
        try {
            let result;
            switch (extension) {
                case 'gltf':
                case 'glb':
                    result = await this.loadGLTF(url, position, scale);
                    break;
                case 'obj':
                    result = await this.loadOBJ(url, null, position, scale);
                    break;
                case 'fbx':
                    result = await this.loadFBX(url, position, scale);
                    break;
                default:
                    throw new Error(`不支持的文件格式: ${extension}`);
            }
            
            // 释放URL
            URL.revokeObjectURL(url);
            return result;
        } catch (error) {
            URL.revokeObjectURL(url);
            throw error;
        }
    }
}
