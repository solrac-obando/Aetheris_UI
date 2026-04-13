/**
 * Aetheris JS Renderer - Lightweight Canvas 2D / WebGL Renderer
 * 
 * This module provides a lightweight JavaScript renderer (~200KB) that can render
 * thousands of elements using either Canvas 2D or WebGL.
 * 
 * @version 1.0.0
 * @license Apache-2.0
 */

(function(global) {
    'use strict';

    const AetherRenderer = {
        renderer: null,
        canvas: null,
        gl: null,
        ctx: null,
        useWebGL: false,
        maxElements: 10000,
        elementCount: 0,
        
        config: {
            width: 1280,
            height: 720,
            backgroundColor: '#000000',
            antialias: true,
            preserveDrawingBuffer: false,
        },

        init: function(options) {
            options = options || {};
            this.config = Object.assign({}, this.config, options);
            
            this.canvas = document.getElementById(this.config.canvasId) || document.createElement('canvas');
            this.canvas.width = this.config.width;
            this.canvas.height = this.config.height;
            
            this.useWebGL = this._detectWebGL();
            
            if (this.useWebGL) {
                this._initWebGL();
            } else {
                this._initCanvas2D();
            }
            
            return this;
        },

        _detectWebGL: function() {
            try {
                const canvas = document.createElement('canvas');
                return !!(
                    canvas.getContext('webgl2') || 
                    canvas.getContext('webgl') || 
                    canvas.getContext('experimental-webgl')
                );
            } catch (e) {
                return false;
            }
        },

        _initCanvas2D: function() {
            this.ctx = this.canvas.getContext('2d', {
                alpha: true,
                antialias: this.config.antialias,
                preserveDrawingBuffer: this.config.preserveDrawingBuffer,
            });
            this.renderer = 'canvas2d';
            console.log('[AetherRenderer] Using Canvas 2D');
        },

        _initWebGL: function() {
            const contextOptions = {
                alpha: true,
                antialias: true,
                premultipliedAlpha: true,
                preserveDrawingBuffer: false,
                depth: false,
                stencil: false,
                failIfMajorPerformanceCaveat: false,
            };
            
            this.gl = this.canvas.getContext('webgl2', contextOptions) || 
                    this.canvas.getContext('webgl', contextOptions) ||
                    this.canvas.getContext('experimental-webgl', contextOptions);
            
            if (this.gl) {
                this._initShaders();
                this._initBuffers();
                this.renderer = 'webgl';
                console.log('[AetherRenderer] Using WebGL');
            } else {
                this._initCanvas2D();
            }
        },

        _initShaders: function() {
            const gl = this.gl;
            
            const vertexShaderSource = `
                attribute vec2 a_position;
                attribute vec2 a_size;
                attribute vec4 a_color;
                
                uniform vec2 u_resolution;
                
                varying vec4 v_color;
                
                void main() {
                    vec2 zeroToOne = a_position / u_resolution;
                    vec2 zeroToTwo = zeroToOne * 2.0;
                    vec2 clipSpace = zeroToTwo - 1.0;
                    
                    gl_Position = vec4(clipSpace * vec2(1, -1), 0, 1);
                    v_color = a_color;
                }
            `;
            
            const fragmentShaderSource = `
                precision mediump float;
                
                varying vec4 v_color;
                
                void main() {
                    gl_FragColor = v_color;
                }
            `;
            
            const vertexShader = this._compileShader(gl.VERTEX_SHADER, vertexShaderSource);
            const fragmentShader = this._compileShader(gl.FRAGMENT_SHADER, fragmentShaderSource);
            
            this.program = gl.createProgram();
            gl.attachShader(this.program, vertexShader);
            gl.attachShader(this.program, fragmentShader);
            gl.linkProgram(this.program);
            
            if (!gl.getProgramParameter(this.program, gl.LINK_STATUS)) {
                console.error('[AetherRenderer] Program link error:', gl.getProgramInfoLog(this.program));
                return false;
            }
            
            gl.useProgram(this.program);
            
            this.a_position = gl.getAttribLocation(this.program, 'a_position');
            this.a_size = gl.getAttribLocation(this.program, 'a_size');
            this.a_color = gl.getAttribLocation(this.program, 'a_color');
            this.u_resolution = gl.getUniformLocation(this.program, 'u_resolution');
            
            gl.uniform2f(this.u_resolution, this.canvas.width, this.canvas.height);
            
            return true;
        },

        _compileShader: function(type, source) {
            const gl = this.gl;
            const shader = gl.createShader(type);
            gl.shaderSource(shader, source);
            gl.compileShader(shader);
            
            if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
                console.error('[AetherRenderer] Shader compile error:', gl.getShaderInfoLog(shader));
                gl.deleteShader(shader);
                return null;
            }
            
            return shader;
        },

        _initBuffers: function() {
            const gl = this.gl;
            
            this.positionBuffer = gl.createBuffer();
            this.sizeBuffer = gl.createBuffer();
            this.colorBuffer = gl.createBuffer();
            
            this.maxElements = Math.min(this.maxElements, 100000);
        },

        render: function(elements) {
            if (!elements || !elements.length) return this;
            
            this.elementCount = elements.length;
            
            if (this.renderer === 'webgl' && this.gl) {
                this._renderWebGL(elements);
            } else if (this.ctx) {
                this._renderCanvas2D(elements);
            }
            
            return this;
        },

        _renderCanvas2D: function(elements) {
            const ctx = this.ctx;
            
            ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            
            elements.sort((a, b) => (a.z || 0) - (b.z || 0));
            
            for (const elem of elements) {
                const x = elem.x || 0;
                const y = elem.y || 0;
                const w = elem.w || 0;
                const h = elem.h || 0;
                const color = elem.color || '#ffffff';
                const opacity = elem.opacity !== undefined ? elem.opacity : 1;
                
                ctx.globalAlpha = opacity;
                ctx.fillStyle = color;
                ctx.fillRect(x, y, w, h);
            }
            
            ctx.globalAlpha = 1;
        },

        _renderWebGL: function(elements) {
            const gl = this.gl;
            
            gl.viewport(0, 0, this.canvas.width, this.canvas.height);
            gl.clearColor(0, 0, 0, 1);
            gl.clear(gl.COLOR_BUFFER_BIT);
            
            const positions = new Float32Array(elements.length * 2);
            const sizes = new Float32Array(elements.length * 2);
            const colors = new Float32Array(elements.length * 4);
            
            elements.sort((a, b) => (a.z || 0) - (b.z || 0));
            
            for (let i = 0; i < elements.length; i++) {
                const elem = elements[i];
                positions[i * 2] = elem.x || 0;
                positions[i * 2 + 1] = elem.y || 0;
                sizes[i * 2] = elem.w || 0;
                sizes[i * 2 + 1] = elem.h || 0;
                
                const color = this._parseColor(elem.color || '#ffffff');
                colors[i * 4] = color[0];
                colors[i * 4 + 1] = color[1];
                colors[i * 4 + 2] = color[2];
                colors[i * 4 + 3] = elem.opacity !== undefined ? elem.opacity : 1;
            }
            
            gl.enable(gl.BLEND);
            gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
            
            gl.bindBuffer(gl.ARRAY_BUFFER, this.positionBuffer);
            gl.bufferData(gl.ARRAY_BUFFER, positions, gl.DYNAMIC_DRAW);
            gl.enableVertexAttribArray(this.a_position);
            gl.vertexAttribPointer(this.a_position, 2, gl.FLOAT, false, 0, 0);
            
            gl.bindBuffer(gl.ARRAY_BUFFER, this.sizeBuffer);
            gl.bufferData(gl.ARRAY_BUFFER, sizes, gl.DYNAMIC_DRAW);
            gl.enableVertexAttribArray(this.a_size);
            gl.vertexAttribPointer(this.a_size, 2, gl.FLOAT, false, 0, 0);
            
            gl.bindBuffer(gl.ARRAY_BUFFER, this.colorBuffer);
            gl.bufferData(gl.ARRAY_BUFFER, colors, gl.DYNAMIC_DRAW);
            gl.enableVertexAttribArray(this.a_color);
            gl.vertexAttribPointer(this.a_color, 4, gl.FLOAT, false, 0, 0);
            
            gl.drawArrays(gl.TRIANGLES, 0, elements.length * 6);
        },

        _parseColor: function(color) {
            if (color.startsWith('#')) {
                const hex = color.slice(1);
                if (hex.length === 3) {
                    return [
                        parseInt(hex[0] + hex[0], 16) / 255,
                        parseInt(hex[1] + hex[1], 16) / 255,
                        parseInt(hex[2] + hex[2], 16) / 255,
                        1
                    ];
                } else if (hex.length === 6) {
                    return [
                        parseInt(hex.slice(0, 2), 16) / 255,
                        parseInt(hex.slice(2, 4), 16) / 255,
                        parseInt(hex.slice(4, 6), 16) / 255,
                        1
                    ];
                }
            }
            return [1, 1, 1, 1];
        },

        clear: function() {
            if (this.ctx) {
                this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            } else if (this.gl) {
                this.gl.clear(this.gl.COLOR_BUFFER_BIT);
            }
            return this;
        },

        resize: function(width, height) {
            this.canvas.width = width;
            this.canvas.height = height;
            
            if (this.gl) {
                this.gl.viewport(0, 0, width, height);
            }
            
            return this;
        },

        destroy: function() {
            if (this.ctx) {
                this.ctx = null;
            }
            if (this.gl) {
                this.gl.deleteProgram(this.program);
                this.gl = null;
            }
            this.canvas = null;
            this.renderer = null;
        },

        getStats: function() {
            return {
                renderer: this.renderer,
                elements: this.elementCount,
                canvas: !!this.ctx,
                webgl: !!this.gl,
                width: this.canvas ? this.canvas.width : 0,
                height: this.canvas ? this.canvas.height : 0,
            };
        }
    };

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = AetherRenderer;
    } else {
        global.AetherRenderer = AetherRenderer;
    }

})(typeof window !== 'undefined' ? window : this);