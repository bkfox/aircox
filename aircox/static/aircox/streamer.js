/******/ (function(modules) { // webpackBootstrap
/******/ 	// install a JSONP callback for chunk loading
/******/ 	function webpackJsonpCallback(data) {
/******/ 		var chunkIds = data[0];
/******/ 		var moreModules = data[1];
/******/ 		var executeModules = data[2];
/******/
/******/ 		// add "moreModules" to the modules object,
/******/ 		// then flag all "chunkIds" as loaded and fire callback
/******/ 		var moduleId, chunkId, i = 0, resolves = [];
/******/ 		for(;i < chunkIds.length; i++) {
/******/ 			chunkId = chunkIds[i];
/******/ 			if(Object.prototype.hasOwnProperty.call(installedChunks, chunkId) && installedChunks[chunkId]) {
/******/ 				resolves.push(installedChunks[chunkId][0]);
/******/ 			}
/******/ 			installedChunks[chunkId] = 0;
/******/ 		}
/******/ 		for(moduleId in moreModules) {
/******/ 			if(Object.prototype.hasOwnProperty.call(moreModules, moduleId)) {
/******/ 				modules[moduleId] = moreModules[moduleId];
/******/ 			}
/******/ 		}
/******/ 		if(parentJsonpFunction) parentJsonpFunction(data);
/******/
/******/ 		while(resolves.length) {
/******/ 			resolves.shift()();
/******/ 		}
/******/
/******/ 		// add entry modules from loaded chunk to deferred list
/******/ 		deferredModules.push.apply(deferredModules, executeModules || []);
/******/
/******/ 		// run deferred modules when all chunks ready
/******/ 		return checkDeferredModules();
/******/ 	};
/******/ 	function checkDeferredModules() {
/******/ 		var result;
/******/ 		for(var i = 0; i < deferredModules.length; i++) {
/******/ 			var deferredModule = deferredModules[i];
/******/ 			var fulfilled = true;
/******/ 			for(var j = 1; j < deferredModule.length; j++) {
/******/ 				var depId = deferredModule[j];
/******/ 				if(installedChunks[depId] !== 0) fulfilled = false;
/******/ 			}
/******/ 			if(fulfilled) {
/******/ 				deferredModules.splice(i--, 1);
/******/ 				result = __webpack_require__(__webpack_require__.s = deferredModule[0]);
/******/ 			}
/******/ 		}
/******/
/******/ 		return result;
/******/ 	}
/******/
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// object to store loaded and loading chunks
/******/ 	// undefined = chunk not loaded, null = chunk preloaded/prefetched
/******/ 	// Promise = chunk loading, 0 = chunk loaded
/******/ 	var installedChunks = {
/******/ 		"streamer": 0
/******/ 	};
/******/
/******/ 	var deferredModules = [];
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId]) {
/******/ 			return installedModules[moduleId].exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			i: moduleId,
/******/ 			l: false,
/******/ 			exports: {}
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.l = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// define getter function for harmony exports
/******/ 	__webpack_require__.d = function(exports, name, getter) {
/******/ 		if(!__webpack_require__.o(exports, name)) {
/******/ 			Object.defineProperty(exports, name, { enumerable: true, get: getter });
/******/ 		}
/******/ 	};
/******/
/******/ 	// define __esModule on exports
/******/ 	__webpack_require__.r = function(exports) {
/******/ 		if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 			Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 		}
/******/ 		Object.defineProperty(exports, '__esModule', { value: true });
/******/ 	};
/******/
/******/ 	// create a fake namespace object
/******/ 	// mode & 1: value is a module id, require it
/******/ 	// mode & 2: merge all properties of value into the ns
/******/ 	// mode & 4: return value when already ns object
/******/ 	// mode & 8|1: behave like require
/******/ 	__webpack_require__.t = function(value, mode) {
/******/ 		if(mode & 1) value = __webpack_require__(value);
/******/ 		if(mode & 8) return value;
/******/ 		if((mode & 4) && typeof value === 'object' && value && value.__esModule) return value;
/******/ 		var ns = Object.create(null);
/******/ 		__webpack_require__.r(ns);
/******/ 		Object.defineProperty(ns, 'default', { enumerable: true, value: value });
/******/ 		if(mode & 2 && typeof value != 'string') for(var key in value) __webpack_require__.d(ns, key, function(key) { return value[key]; }.bind(null, key));
/******/ 		return ns;
/******/ 	};
/******/
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__webpack_require__.n = function(module) {
/******/ 		var getter = module && module.__esModule ?
/******/ 			function getDefault() { return module['default']; } :
/******/ 			function getModuleExports() { return module; };
/******/ 		__webpack_require__.d(getter, 'a', getter);
/******/ 		return getter;
/******/ 	};
/******/
/******/ 	// Object.prototype.hasOwnProperty.call
/******/ 	__webpack_require__.o = function(object, property) { return Object.prototype.hasOwnProperty.call(object, property); };
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "";
/******/
/******/ 	var jsonpArray = window["webpackJsonp"] = window["webpackJsonp"] || [];
/******/ 	var oldJsonpFunction = jsonpArray.push.bind(jsonpArray);
/******/ 	jsonpArray.push = webpackJsonpCallback;
/******/ 	jsonpArray = jsonpArray.slice();
/******/ 	for(var i = 0; i < jsonpArray.length; i++) webpackJsonpCallback(jsonpArray[i]);
/******/ 	var parentJsonpFunction = oldJsonpFunction;
/******/
/******/
/******/ 	// add entry module to deferred list
/******/ 	deferredModules.push(["./assets/streamer/index.js","vendor"]);
/******/ 	// run deferred modules when ready
/******/ 	return checkDeferredModules();
/******/ })
/************************************************************************/
/******/ ({

/***/ "./assets/public/app.js":
/*!******************************!*\
  !*** ./assets/public/app.js ***!
  \******************************/
/*! exports provided: appBaseConfig, setAppConfig, getAppConfig, loadApp */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"appBaseConfig\", function() { return appBaseConfig; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"setAppConfig\", function() { return setAppConfig; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"getAppConfig\", function() { return getAppConfig; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"loadApp\", function() { return loadApp; });\n/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! vue */ \"./node_modules/vue/dist/vue.esm.browser.js\");\n\n\n\nconst appBaseConfig = {\n    el: '#app',\n    delimiters: ['[[', ']]'],\n}\n\n/**\n * Application config for the main application instance\n */\nvar appConfig = {};\n\nfunction setAppConfig(config) {\n    for(var member in appConfig) delete appConfig[member];\n    return Object.assign(appConfig, config)\n}\n\nfunction getAppConfig(config) {\n    if(config instanceof Function)\n        config = config()\n    config = config == null ? appConfig : config;\n    return {...appBaseConfig, ...config}\n}\n\n\n/**\n * Create Vue application at window 'load' event and return a Promise\n * resolving to the created app.\n *\n * config: defaults to appConfig (checked when window is loaded)\n */\nfunction loadApp(config=null) {\n    return new Promise(function(resolve, reject) {\n        window.addEventListener('load', function() {\n            try {\n                config = getAppConfig(config)\n                const el = document.querySelector(config.el)\n                if(!el) {\n                    reject(`Error: missing element ${config.el}`);\n                    return;\n                }\n\n                resolve(new vue__WEBPACK_IMPORTED_MODULE_0__[\"default\"](config))\n            }\n            catch(error) { reject(error) }\n        })\n    })\n}\n\n\n\n\n\n\n//# sourceURL=webpack:///./assets/public/app.js?");

/***/ }),

/***/ "./assets/public/model.js":
/*!********************************!*\
  !*** ./assets/public/model.js ***!
  \********************************/
/*! exports provided: getCsrf, default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"getCsrf\", function() { return getCsrf; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"default\", function() { return Model; });\n/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! vue */ \"./node_modules/vue/dist/vue.esm.browser.js\");\n\n\nfunction getCookie(name) {\n    if(document.cookie && document.cookie !== '') {\n        const cookie = document.cookie.split(';')\n                               .find(c => c.trim().startsWith(name + '='))\n        return cookie ? decodeURIComponent(cookie.split('=')[1]) : null;\n    }\n    return null;\n}\n\nvar csrfToken = null;\n\nfunction getCsrf() {\n    if(csrfToken === null)\n        csrfToken = getCookie('csrftoken')\n    return csrfToken;\n}\n\n\n// TODO: move in another module for reuse\n// TODO: prevent duplicate simple fetch\nclass Model {\n    constructor(data, {url=null}={}) {\n        this.commit(data);\n    }\n\n    static getId(data) {\n        return data.id;\n    }\n\n    static getOptions(options) {\n        return {\n            headers: {\n                'Content-Type': 'application/json',\n                'Accept': 'application/json',\n                'X-CSRFToken': getCsrf(),\n            },\n            ...options,\n        }\n    }\n\n    static fetch(url, options=null, initArgs=null) {\n        options = this.getOptions(options)\n        return fetch(url, options)\n            .then(response => response.json())\n            .then(data => new this(d, {url: url, ...initArgs}));\n    }\n\n    static fetchAll(url, options=null, initArgs=null) {\n        options = this.getOptions(options)\n        return fetch(url, options)\n            .then(response => response.json())\n            .then(data => {\n                if(!(data instanceof Array))\n                    data = data.results;\n                data = data.map(d => new this(d, {baseUrl: url, ...initArgs}));\n                return data\n            })\n    }\n\n    /**\n     * Fetch data from server.\n     */\n    fetch(options) {\n        options = this.constructor.getOptions(options)\n        return fetch(this.url, options)\n            .then(response => response.json())\n            .then(data => this.commit(data));\n    }\n\n    /**\n     * Call API action on object.\n     */\n    action(path, options, commit=false) {\n        options = this.constructor.getOptions(options)\n        const promise = fetch(this.url + path, options);\n        return commit ? promise.then(data => data.json())\n                               .then(data => { this.commit(data); this.data })\n                      : promise;\n    }\n\n    /**\n     * Update instance's data with provided data. Return None\n     */\n    commit(data) {\n        this.id = this.constructor.getId(data);\n        this.url = data.url_;\n        vue__WEBPACK_IMPORTED_MODULE_0__[\"default\"].set(this, 'data', data);\n    }\n\n    /**\n     * Return data as model with url prepent by `this.url`.\n     */\n    asChild(model, data, prefix='') {\n        return new model(data, {baseUrl: `${this.url}${prefix}/`})\n    }\n\n    getChildOf(attr, id) {\n        const index = this.data[attr].findIndex(o => o.id = id)\n        return index == -1 ? null : this.data[attr][index];\n    }\n\n    static updateList(list=[], old=[], ...initArgs) {\n         return list.reduce((items, data) => {\n            const id = this.getId(data);\n            let [index, obj] = [old.findIndex(o => o.id == id), null];\n            if(index != -1) {\n                old[index].commit(data)\n                items.push(old[index]);\n            }\n            else\n                items.push(new this(data, ...initArgs))\n            return items;\n        }, [])\n    }\n}\n\n\n\n\n//# sourceURL=webpack:///./assets/public/model.js?");

/***/ }),

/***/ "./assets/public/sound.js":
/*!********************************!*\
  !*** ./assets/public/sound.js ***!
  \********************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"default\", function() { return Sound; });\n/* harmony import */ var _model__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./model */ \"./assets/public/model.js\");\n\n\n\nclass Sound extends _model__WEBPACK_IMPORTED_MODULE_0__[\"default\"] {\n    get name() { return this.data.name }\n\n    static getId(data) { return data.pk }\n}\n\n\n\n\n//# sourceURL=webpack:///./assets/public/sound.js?");

/***/ }),

/***/ "./assets/public/utils.js":
/*!********************************!*\
  !*** ./assets/public/utils.js ***!
  \********************************/
/*! exports provided: setEcoTimeout, setEcoInterval */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"setEcoTimeout\", function() { return setEcoTimeout; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"setEcoInterval\", function() { return setEcoInterval; });\n\n\nfunction setEcoTimeout(func, ...args) {\n    return setTimeout((...args) => {\n        !document.hidden && func(...args)\n    }, ...args)\n}\n\n\nfunction setEcoInterval(func, ...args) {\n    return setInterval((...args) => {\n        !document.hidden && func(...args)\n    }, ...args)\n}\n\n\n\n//# sourceURL=webpack:///./assets/public/utils.js?");

/***/ }),

/***/ "./assets/streamer/controllers.js":
/*!****************************************!*\
  !*** ./assets/streamer/controllers.js ***!
  \****************************************/
/*! exports provided: Streamer, Request, Source, Playlist, Queue */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"Streamer\", function() { return Streamer; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"Request\", function() { return Request; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"Source\", function() { return Source; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"Playlist\", function() { return Playlist; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"Queue\", function() { return Queue; });\n/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! vue */ \"./node_modules/vue/dist/vue.esm.browser.js\");\n/* harmony import */ var public_model__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! public/model */ \"./assets/public/model.js\");\n/* harmony import */ var public_utils__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! public/utils */ \"./assets/public/utils.js\");\n\n\n\n\n\n\nclass Streamer extends public_model__WEBPACK_IMPORTED_MODULE_1__[\"default\"] {\n    get queues() { return this.data ? this.data.queues : []; }\n    get playlists() { return this.data ? this.data.playlists : []; }\n    get sources() { return [...this.queues, ...this.playlists]; }\n    get source() { return this.sources.find(o => o.id == this.data.source) }\n\n    commit(data) {\n        if(!this.data)\n            this.data = { id: data.id, playlists: [], queues: [] }\n\n        data.playlists = Playlist.updateList(data.playlists, this.playlists, {streamer: this})\n        data.queues = Queue.updateList(data.queues, this.queues, {streamer: this})\n        super.commit(data)\n    }\n}\n\nclass Request extends public_model__WEBPACK_IMPORTED_MODULE_1__[\"default\"] {\n    static getId(data) { return data.rid; }\n}\n\nclass Source extends public_model__WEBPACK_IMPORTED_MODULE_1__[\"default\"] {\n    constructor(data, {streamer=null, ...options}={}) {\n        super(data, options);\n        this.streamer = streamer;\n        Object(public_utils__WEBPACK_IMPORTED_MODULE_2__[\"setEcoInterval\"])(() => this.tick(), 1000)\n    }\n\n    get isQueue() { return false; }\n    get isPlaylist() { return false; }\n    get isPlaying() { return this.data.status == 'playing' }\n    get isPaused() { return this.data.status == 'paused' }\n\n    get remainingString() {\n        if(!this.remaining)\n            return '00:00';\n\n        const seconds = Math.floor(this.remaining % 60);\n        const minutes = Math.floor(this.remaining / 60);\n        return String(minutes).padStart(2, '0') + ':' +\n               String(seconds).padStart(2, '0');\n    }\n\n    sync() { return this.action('sync/', {method: 'POST'}, true); }\n    skip() { return this.action('skip/', {method: 'POST'}, true); }\n    restart() { return this.action('restart/', {method: 'POST'}, true); }\n\n    seek(count) {\n        return this.action('seek/', {\n            method: 'POST',\n            body: JSON.stringify({count: count})\n        }, true)\n    }\n\n    tick() {\n        if(!this.data.remaining || !this.isPlaying)\n            return;\n        const delta = (Date.now() - this.commitDate) / 1000;\n        vue__WEBPACK_IMPORTED_MODULE_0__[\"default\"].set(this, 'remaining', this.data.remaining - delta)\n    }\n\n    commit(data) {\n        if(data.air_time)\n            data.air_time = new Date(data.air_time);\n\n        this.commitDate = Date.now()\n        super.commit(data)\n        vue__WEBPACK_IMPORTED_MODULE_0__[\"default\"].set(this, 'remaining', data.remaining)\n    }\n}\n\n\nclass Playlist extends Source {\n    get isPlaylist() { return true; }\n}\n\n\nclass Queue extends Source {\n    get isQueue() { return true; }\n    get queue() { return this.data && this.data.queue; }\n\n    commit(data) {\n        data.queue = Request.updateList(data.queue, this.queue)\n        super.commit(data)\n    }\n\n    push(soundId) {\n        return this.action('push/', {\n            method: 'POST',\n            body: JSON.stringify({'sound_id': parseInt(soundId)})\n        }, true);\n    }\n}\n\n\n\n\n//# sourceURL=webpack:///./assets/streamer/controllers.js?");

/***/ }),

/***/ "./assets/streamer/index.js":
/*!**********************************!*\
  !*** ./assets/streamer/index.js ***!
  \**********************************/
/*! no exports provided */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! vue */ \"./node_modules/vue/dist/vue.esm.browser.js\");\n/* harmony import */ var buefy_dist_components_button__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! buefy/dist/components/button */ \"./node_modules/buefy/dist/components/button/index.js\");\n/* harmony import */ var buefy_dist_components_button__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(buefy_dist_components_button__WEBPACK_IMPORTED_MODULE_1__);\n/* harmony import */ var public_app__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! public/app */ \"./assets/public/app.js\");\n/* harmony import */ var public_model__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! public/model */ \"./assets/public/model.js\");\n/* harmony import */ var public_sound__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! public/sound */ \"./assets/public/sound.js\");\n/* harmony import */ var public_utils__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! public/utils */ \"./assets/public/utils.js\");\n/* harmony import */ var _controllers__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./controllers */ \"./assets/streamer/controllers.js\");\n\n\n\nvue__WEBPACK_IMPORTED_MODULE_0__[\"default\"].use(buefy_dist_components_button__WEBPACK_IMPORTED_MODULE_1___default.a)\n\n\n\n\n\n\n\n\nwindow.aircox.appConfig = {\n    data() {\n        return {\n            // current streamer\n            streamer: null,\n            // all streamers\n            streamers: [],\n            // fetch interval id\n            fetchInterval: null,\n\n            Sound: public_sound__WEBPACK_IMPORTED_MODULE_4__[\"default\"],\n        }\n    },\n\n    computed: {\n        apiUrl() {\n            return this.$el && this.$el.dataset.apiUrl;\n        },\n\n        sources() {\n            var sources = this.streamer ? this.streamer.sources : [];\n            return sources.filter(s => s.data)\n        },\n    },\n\n    methods: {\n        fetchStreamers() {\n            _controllers__WEBPACK_IMPORTED_MODULE_6__[\"Streamer\"].fetchAll(this.apiUrl, null)\n                .then(streamers => {\n                    vue__WEBPACK_IMPORTED_MODULE_0__[\"default\"].set(this, 'streamers', streamers);\n                    vue__WEBPACK_IMPORTED_MODULE_0__[\"default\"].set(this, 'streamer', streamers ? streamers[0] : null);\n                })\n        },\n    },\n\n    mounted() {\n        this.fetchStreamers();\n        this.fetchInterval = Object(public_utils__WEBPACK_IMPORTED_MODULE_5__[\"setEcoInterval\"])(() => this.streamer && this.streamer.fetch(), 5000)\n    },\n\n    destroyed() {\n        if(this.fetchInterval !== null)\n            clearInterval(this.fetchInterval)\n    }\n}\n\n\n\n//# sourceURL=webpack:///./assets/streamer/index.js?");

/***/ })

/******/ });