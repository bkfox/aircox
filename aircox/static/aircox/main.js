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
/******/ 		"main": 0
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
/******/ 	deferredModules.push(["./assets/public/index.js","vendor"]);
/******/ 	// run deferred modules when ready
/******/ 	return checkDeferredModules();
/******/ })
/************************************************************************/
/******/ ({

/***/ "./assets/public/app.js":
/*!******************************!*\
  !*** ./assets/public/app.js ***!
  \******************************/
/*! exports provided: app, default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"app\", function() { return app; });\n/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! vue */ \"./node_modules/vue/dist/vue.esm.browser.js\");\n\n\n\nvar app = null;\n/* harmony default export */ __webpack_exports__[\"default\"] = (app);\n\nfunction loadApp() {\n    app = new vue__WEBPACK_IMPORTED_MODULE_0__[\"default\"]({\n      el: '#app',\n      delimiters: [ '[[', ']]' ],\n    })\n}\n\nwindow.addEventListener('load', loadApp);\n\n\n\n\n\n//# sourceURL=webpack:///./assets/public/app.js?");

/***/ }),

/***/ "./assets/public/index.js":
/*!********************************!*\
  !*** ./assets/public/index.js ***!
  \********************************/
/*! no exports provided */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! vue */ \"./node_modules/vue/dist/vue.esm.browser.js\");\n/* harmony import */ var _fortawesome_fontawesome_free_css_all_min_css__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @fortawesome/fontawesome-free/css/all.min.css */ \"./node_modules/@fortawesome/fontawesome-free/css/all.min.css\");\n/* harmony import */ var _fortawesome_fontawesome_free_css_all_min_css__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_fortawesome_fontawesome_free_css_all_min_css__WEBPACK_IMPORTED_MODULE_1__);\n/* harmony import */ var _fortawesome_fontawesome_free_css_fontawesome_min_css__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @fortawesome/fontawesome-free/css/fontawesome.min.css */ \"./node_modules/@fortawesome/fontawesome-free/css/fontawesome.min.css\");\n/* harmony import */ var _fortawesome_fontawesome_free_css_fontawesome_min_css__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_fortawesome_fontawesome_free_css_fontawesome_min_css__WEBPACK_IMPORTED_MODULE_2__);\n/* harmony import */ var buefy_dist_buefy_css__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! buefy/dist/buefy.css */ \"./node_modules/buefy/dist/buefy.css\");\n/* harmony import */ var buefy_dist_buefy_css__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(buefy_dist_buefy_css__WEBPACK_IMPORTED_MODULE_3__);\n/* harmony import */ var _app__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./app */ \"./assets/public/app.js\");\n/* harmony import */ var _liveInfo__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./liveInfo */ \"./assets/public/liveInfo.js\");\n/* harmony import */ var _styles_scss__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./styles.scss */ \"./assets/public/styles.scss\");\n/* harmony import */ var _styles_scss__WEBPACK_IMPORTED_MODULE_6___default = /*#__PURE__*/__webpack_require__.n(_styles_scss__WEBPACK_IMPORTED_MODULE_6__);\n/* harmony import */ var _player_vue__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./player.vue */ \"./assets/public/player.vue\");\n/**\n * This module includes code available for both the public website and\n * administration interface)\n */\n//-- vendor\n\n\n\n\n\n\n\n//-- aircox\n\n\n\n\n\n\n\nvue__WEBPACK_IMPORTED_MODULE_0__[\"default\"].component('a-player', _player_vue__WEBPACK_IMPORTED_MODULE_7__[\"default\"])\n\n\nwindow.aircox = {\n    app: _app__WEBPACK_IMPORTED_MODULE_4__[\"default\"],\n    LiveInfo: _liveInfo__WEBPACK_IMPORTED_MODULE_5__[\"default\"],\n}\n\n\n\n//# sourceURL=webpack:///./assets/public/index.js?");

/***/ }),

/***/ "./assets/public/liveInfo.js":
/*!***********************************!*\
  !*** ./assets/public/liveInfo.js ***!
  \***********************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n\n/* harmony default export */ __webpack_exports__[\"default\"] = (class {\n    constructor(url, timeout) {\n        this.url = url;\n        this.timeout = timeout;\n        this.promise = null;\n        this.items = [];\n    }\n\n    drop() {\n        this.promise = null;\n    }\n\n    fetch() {\n        const promise = fetch(this.url).then(response =>\n            response.ok ? response.json()\n                        : Promise.reject(response)\n        ).then(data => {\n            this.items = data;\n            return this.items\n        })\n\n        this.promise = promise;\n        return promise;\n    }\n\n    refresh() {\n        const promise = this.fetch();\n        promise.then(data => {\n            if(promise != this.promise)\n                return [];\n\n            window.setTimeout(() => this.refresh(), this.timeout*1000)\n        })\n        return promise\n    }\n});\n\n\n//# sourceURL=webpack:///./assets/public/liveInfo.js?");

/***/ }),

/***/ "./assets/public/player.vue":
/*!**********************************!*\
  !*** ./assets/public/player.vue ***!
  \**********************************/
/*! exports provided: default, State */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _player_vue_vue_type_template_id_42a56ec9___WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./player.vue?vue&type=template&id=42a56ec9& */ \"./assets/public/player.vue?vue&type=template&id=42a56ec9&\");\n/* harmony import */ var _player_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./player.vue?vue&type=script&lang=js& */ \"./assets/public/player.vue?vue&type=script&lang=js&\");\n/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, \"State\", function() { return _player_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_1__[\"State\"]; });\n\n/* harmony import */ var _node_modules_vue_loader_lib_runtime_componentNormalizer_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../node_modules/vue-loader/lib/runtime/componentNormalizer.js */ \"./node_modules/vue-loader/lib/runtime/componentNormalizer.js\");\n\n\n\n\n\n/* normalize component */\n\nvar component = Object(_node_modules_vue_loader_lib_runtime_componentNormalizer_js__WEBPACK_IMPORTED_MODULE_2__[\"default\"])(\n  _player_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_1__[\"default\"],\n  _player_vue_vue_type_template_id_42a56ec9___WEBPACK_IMPORTED_MODULE_0__[\"render\"],\n  _player_vue_vue_type_template_id_42a56ec9___WEBPACK_IMPORTED_MODULE_0__[\"staticRenderFns\"],\n  false,\n  null,\n  null,\n  null\n  \n)\n\n/* hot reload */\nif (false) { var api; }\ncomponent.options.__file = \"assets/public/player.vue\"\n/* harmony default export */ __webpack_exports__[\"default\"] = (component.exports);\n\n//# sourceURL=webpack:///./assets/public/player.vue?");

/***/ }),

/***/ "./assets/public/player.vue?vue&type=script&lang=js&":
/*!***********************************************************!*\
  !*** ./assets/public/player.vue?vue&type=script&lang=js& ***!
  \***********************************************************/
/*! exports provided: default, State */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _node_modules_vue_loader_lib_index_js_vue_loader_options_player_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../node_modules/vue-loader/lib??vue-loader-options!./player.vue?vue&type=script&lang=js& */ \"./node_modules/vue-loader/lib/index.js?!./assets/public/player.vue?vue&type=script&lang=js&\");\n/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, \"State\", function() { return _node_modules_vue_loader_lib_index_js_vue_loader_options_player_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_0__[\"State\"]; });\n\n /* harmony default export */ __webpack_exports__[\"default\"] = (_node_modules_vue_loader_lib_index_js_vue_loader_options_player_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_0__[\"default\"]); \n\n//# sourceURL=webpack:///./assets/public/player.vue?");

/***/ }),

/***/ "./assets/public/player.vue?vue&type=template&id=42a56ec9&":
/*!*****************************************************************!*\
  !*** ./assets/public/player.vue?vue&type=template&id=42a56ec9& ***!
  \*****************************************************************/
/*! exports provided: render, staticRenderFns */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _node_modules_vue_loader_lib_loaders_templateLoader_js_vue_loader_options_node_modules_vue_loader_lib_index_js_vue_loader_options_player_vue_vue_type_template_id_42a56ec9___WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../node_modules/vue-loader/lib/loaders/templateLoader.js??vue-loader-options!../../node_modules/vue-loader/lib??vue-loader-options!./player.vue?vue&type=template&id=42a56ec9& */ \"./node_modules/vue-loader/lib/loaders/templateLoader.js?!./node_modules/vue-loader/lib/index.js?!./assets/public/player.vue?vue&type=template&id=42a56ec9&\");\n/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, \"render\", function() { return _node_modules_vue_loader_lib_loaders_templateLoader_js_vue_loader_options_node_modules_vue_loader_lib_index_js_vue_loader_options_player_vue_vue_type_template_id_42a56ec9___WEBPACK_IMPORTED_MODULE_0__[\"render\"]; });\n\n/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, \"staticRenderFns\", function() { return _node_modules_vue_loader_lib_loaders_templateLoader_js_vue_loader_options_node_modules_vue_loader_lib_index_js_vue_loader_options_player_vue_vue_type_template_id_42a56ec9___WEBPACK_IMPORTED_MODULE_0__[\"staticRenderFns\"]; });\n\n\n\n//# sourceURL=webpack:///./assets/public/player.vue?");

/***/ }),

/***/ "./assets/public/styles.scss":
/*!***********************************!*\
  !*** ./assets/public/styles.scss ***!
  \***********************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

eval("// extracted by mini-css-extract-plugin\n\n//# sourceURL=webpack:///./assets/public/styles.scss?");

/***/ }),

/***/ "./node_modules/vue-loader/lib/index.js?!./assets/public/player.vue?vue&type=script&lang=js&":
/*!*************************************************************************************************************!*\
  !*** ./node_modules/vue-loader/lib??vue-loader-options!./assets/public/player.vue?vue&type=script&lang=js& ***!
  \*************************************************************************************************************/
/*! exports provided: State, default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"State\", function() { return State; });\n/* harmony import */ var _liveInfo__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./liveInfo */ \"./assets/public/liveInfo.js\");\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n\n\n\nconst State = {\n    paused: 0,\n    playing: 1,\n    loading: 2,\n}\n\n/* harmony default export */ __webpack_exports__[\"default\"] = ({\n    data() {\n        return {\n            state: State.paused,\n            liveInfo: new _liveInfo__WEBPACK_IMPORTED_MODULE_0__[\"default\"](this.liveInfoUrl, this.liveInfoTimeout),\n        }\n    },\n\n    props: {\n        buttonTitle: String,\n        liveInfoUrl: String,\n        liveInfoTimeout: { type: Number, default: 5},\n        src: String,\n    },\n\n    computed: {\n        paused() { return this.state == State.paused; },\n        playing() { return this.state == State.playing; },\n        loading() { return this.state == State.loading; },\n\n        onAir() {\n            return this.liveInfo.items && this.liveInfo.items[0];\n        },\n\n        buttonStyle() {\n            if(!this.onAir)\n                return;\n            return { backgroundImage: `url(${this.onAir.cover})` }\n        }\n    },\n\n    methods: {\n        load(src) {\n            const audio = this.$refs.audio;\n            audio.src = src;\n            audio.load()\n        },\n\n        play(src) {\n            if(src)\n                this.load(src);\n            this.$refs.audio.play().catch(e => console.error(e))\n        },\n\n        pause() {\n            this.$refs.audio.pause()\n        },\n\n        toggle() {\n            console.log('tooogle', this.paused, '-', this.$refs.audio.src)\n            if(this.paused)\n                this.play()\n            else\n                this.pause()\n        },\n\n        onChange(event) {\n            const audio = this.$refs.audio;\n            this.state = audio.paused ? State.paused : State.playing;\n        },\n    },\n\n    mounted() {\n        this.liveInfo.refresh()\n    },\n\n    destroyed() {\n        this.liveInfo.drop()\n    },\n});\n\n\n\n//# sourceURL=webpack:///./assets/public/player.vue?./node_modules/vue-loader/lib??vue-loader-options");

/***/ }),

/***/ "./node_modules/vue-loader/lib/loaders/templateLoader.js?!./node_modules/vue-loader/lib/index.js?!./assets/public/player.vue?vue&type=template&id=42a56ec9&":
/*!***********************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/vue-loader/lib/loaders/templateLoader.js??vue-loader-options!./node_modules/vue-loader/lib??vue-loader-options!./assets/public/player.vue?vue&type=template&id=42a56ec9& ***!
  \***********************************************************************************************************************************************************************************************/
/*! exports provided: render, staticRenderFns */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"render\", function() { return render; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"staticRenderFns\", function() { return staticRenderFns; });\nvar render = function() {\n  var _vm = this\n  var _h = _vm.$createElement\n  var _c = _vm._self._c || _h\n  return _c(\"div\", { staticClass: \"media\" }, [\n    _c(\"div\", { staticClass: \"media-left\" }, [\n      _c(\n        \"div\",\n        {\n          staticClass: \"button\",\n          attrs: { title: _vm.buttonTitle, \"aria-label\": _vm.buttonTitle },\n          on: {\n            click: function($event) {\n              return _vm.toggle()\n            }\n          }\n        },\n        [\n          _vm.playing\n            ? _c(\"span\", { staticClass: \"fas fa-pause\" })\n            : _c(\"span\", { staticClass: \"fas fa-play\" })\n        ]\n      ),\n      _vm._v(\" \"),\n      _c(\n        \"audio\",\n        {\n          ref: \"audio\",\n          on: {\n            playing: _vm.onChange,\n            ended: _vm.onChange,\n            pause: _vm.onChange\n          }\n        },\n        [_vm._t(\"sources\")],\n        2\n      )\n    ]),\n    _vm._v(\" \"),\n    _vm.onAir && _vm.onAir.cover\n      ? _c(\"div\", { staticClass: \"media-left media-cover\" }, [\n          _c(\"img\", { staticClass: \"cover\", attrs: { src: _vm.onAir.cover } })\n        ])\n      : _vm._e(),\n    _vm._v(\" \"),\n    _vm.onAir && _vm.onAir.type == \"track\"\n      ? _c(\n          \"div\",\n          { staticClass: \"media-content\" },\n          [_vm._t(\"track\", null, { onAir: _vm.onAir, liveInfo: _vm.liveInfo })],\n          2\n        )\n      : _vm.onAir && _vm.onAir.type == \"diffusion\"\n      ? _c(\n          \"div\",\n          { staticClass: \"media-content\" },\n          [\n            _vm._t(\"diffusion\", null, {\n              onAir: _vm.onAir,\n              liveInfo: _vm.liveInfo\n            })\n          ],\n          2\n        )\n      : _c(\"div\", { staticClass: \"media-content\" }, [_vm._t(\"empty\")], 2)\n  ])\n}\nvar staticRenderFns = []\nrender._withStripped = true\n\n\n\n//# sourceURL=webpack:///./assets/public/player.vue?./node_modules/vue-loader/lib/loaders/templateLoader.js??vue-loader-options!./node_modules/vue-loader/lib??vue-loader-options");

/***/ })

/******/ });