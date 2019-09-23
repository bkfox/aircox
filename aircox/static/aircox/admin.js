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
/******/ 		"admin": 0
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
/******/ 	deferredModules.push(["./assets/admin/index.js","vendor"]);
/******/ 	// run deferred modules when ready
/******/ 	return checkDeferredModules();
/******/ })
/************************************************************************/
/******/ ({

/***/ "./assets/admin/admin.scss":
/*!*********************************!*\
  !*** ./assets/admin/admin.scss ***!
  \*********************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

eval("// extracted by mini-css-extract-plugin\n\n//# sourceURL=webpack:///./assets/admin/admin.scss?");

/***/ }),

/***/ "./assets/admin/index.js":
/*!*******************************!*\
  !*** ./assets/admin/index.js ***!
  \*******************************/
/*! no exports provided */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! vue */ \"./node_modules/vue/dist/vue.esm.browser.js\");\n/* harmony import */ var _admin_scss__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./admin.scss */ \"./assets/admin/admin.scss\");\n/* harmony import */ var _admin_scss__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_admin_scss__WEBPACK_IMPORTED_MODULE_1__);\n/* harmony import */ var _statistics_vue__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./statistics.vue */ \"./assets/admin/statistics.vue\");\n/* harmony import */ var public__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! public */ \"./assets/public/index.js\");\n\n\n\n\n\n\nvue__WEBPACK_IMPORTED_MODULE_0__[\"default\"].component('a-statistics', _statistics_vue__WEBPACK_IMPORTED_MODULE_2__[\"default\"])\n\n\n\n\n\n\n\n\n//# sourceURL=webpack:///./assets/admin/index.js?");

/***/ }),

/***/ "./assets/admin/statistics.vue":
/*!*************************************!*\
  !*** ./assets/admin/statistics.vue ***!
  \*************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _statistics_vue_vue_type_template_id_47005a51___WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./statistics.vue?vue&type=template&id=47005a51& */ \"./assets/admin/statistics.vue?vue&type=template&id=47005a51&\");\n/* harmony import */ var _statistics_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./statistics.vue?vue&type=script&lang=js& */ \"./assets/admin/statistics.vue?vue&type=script&lang=js&\");\n/* empty/unused harmony star reexport *//* harmony import */ var _node_modules_vue_loader_lib_runtime_componentNormalizer_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../node_modules/vue-loader/lib/runtime/componentNormalizer.js */ \"./node_modules/vue-loader/lib/runtime/componentNormalizer.js\");\n\n\n\n\n\n/* normalize component */\n\nvar component = Object(_node_modules_vue_loader_lib_runtime_componentNormalizer_js__WEBPACK_IMPORTED_MODULE_2__[\"default\"])(\n  _statistics_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_1__[\"default\"],\n  _statistics_vue_vue_type_template_id_47005a51___WEBPACK_IMPORTED_MODULE_0__[\"render\"],\n  _statistics_vue_vue_type_template_id_47005a51___WEBPACK_IMPORTED_MODULE_0__[\"staticRenderFns\"],\n  false,\n  null,\n  null,\n  null\n  \n)\n\n/* hot reload */\nif (false) { var api; }\ncomponent.options.__file = \"assets/admin/statistics.vue\"\n/* harmony default export */ __webpack_exports__[\"default\"] = (component.exports);\n\n//# sourceURL=webpack:///./assets/admin/statistics.vue?");

/***/ }),

/***/ "./assets/admin/statistics.vue?vue&type=script&lang=js&":
/*!**************************************************************!*\
  !*** ./assets/admin/statistics.vue?vue&type=script&lang=js& ***!
  \**************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _node_modules_vue_loader_lib_index_js_vue_loader_options_statistics_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../node_modules/vue-loader/lib??vue-loader-options!./statistics.vue?vue&type=script&lang=js& */ \"./node_modules/vue-loader/lib/index.js?!./assets/admin/statistics.vue?vue&type=script&lang=js&\");\n/* empty/unused harmony star reexport */ /* harmony default export */ __webpack_exports__[\"default\"] = (_node_modules_vue_loader_lib_index_js_vue_loader_options_statistics_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_0__[\"default\"]); \n\n//# sourceURL=webpack:///./assets/admin/statistics.vue?");

/***/ }),

/***/ "./assets/admin/statistics.vue?vue&type=template&id=47005a51&":
/*!********************************************************************!*\
  !*** ./assets/admin/statistics.vue?vue&type=template&id=47005a51& ***!
  \********************************************************************/
/*! exports provided: render, staticRenderFns */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _node_modules_vue_loader_lib_loaders_templateLoader_js_vue_loader_options_node_modules_vue_loader_lib_index_js_vue_loader_options_statistics_vue_vue_type_template_id_47005a51___WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../node_modules/vue-loader/lib/loaders/templateLoader.js??vue-loader-options!../../node_modules/vue-loader/lib??vue-loader-options!./statistics.vue?vue&type=template&id=47005a51& */ \"./node_modules/vue-loader/lib/loaders/templateLoader.js?!./node_modules/vue-loader/lib/index.js?!./assets/admin/statistics.vue?vue&type=template&id=47005a51&\");\n/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, \"render\", function() { return _node_modules_vue_loader_lib_loaders_templateLoader_js_vue_loader_options_node_modules_vue_loader_lib_index_js_vue_loader_options_statistics_vue_vue_type_template_id_47005a51___WEBPACK_IMPORTED_MODULE_0__[\"render\"]; });\n\n/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, \"staticRenderFns\", function() { return _node_modules_vue_loader_lib_loaders_templateLoader_js_vue_loader_options_node_modules_vue_loader_lib_index_js_vue_loader_options_statistics_vue_vue_type_template_id_47005a51___WEBPACK_IMPORTED_MODULE_0__[\"staticRenderFns\"]; });\n\n\n\n//# sourceURL=webpack:///./assets/admin/statistics.vue?");

/***/ }),

/***/ "./assets/public/app.js":
/*!******************************!*\
  !*** ./assets/public/app.js ***!
  \******************************/
/*! exports provided: appBaseConfig, setAppConfig, getAppConfig, loadApp */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"appBaseConfig\", function() { return appBaseConfig; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"setAppConfig\", function() { return setAppConfig; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"getAppConfig\", function() { return getAppConfig; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"loadApp\", function() { return loadApp; });\n/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! vue */ \"./node_modules/vue/dist/vue.esm.browser.js\");\n\n\n\nconst appBaseConfig = {\n    el: '#app',\n    delimiters: ['[[', ']]'],\n}\n\n/**\n * Application config for the main application instance\n */\nvar appConfig = {};\n\nfunction setAppConfig(config) {\n    for(var member in appConfig) delete appConfig[member];\n    return Object.assign(appConfig, config)\n}\n\nfunction getAppConfig(config) {\n    if(config instanceof Function)\n        config = config()\n    config = config == null ? appConfig : config;\n    return {...appBaseConfig, ...config}\n}\n\n\n/**\n * Create Vue application at window 'load' event and return a Promise\n * resolving to the created app.\n *\n * config: defaults to appConfig (checked when window is loaded)\n */\nfunction loadApp(config=null) {\n    return new Promise(function(resolve, reject) {\n        window.addEventListener('load', function() {\n            try {\n                config = getAppConfig(config)\n                const el = document.querySelector(config.el)\n                if(!el) {\n                    reject(`Error: missing element ${config.el}`);\n                    return;\n                }\n\n                resolve(new vue__WEBPACK_IMPORTED_MODULE_0__[\"default\"](config))\n            }\n            catch(error) { reject(error) }\n        })\n    })\n}\n\n\n\n\n\n\n//# sourceURL=webpack:///./assets/public/app.js?");

/***/ }),

/***/ "./assets/public/autocomplete.vue":
/*!****************************************!*\
  !*** ./assets/public/autocomplete.vue ***!
  \****************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _autocomplete_vue_vue_type_template_id_70936760___WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./autocomplete.vue?vue&type=template&id=70936760& */ \"./assets/public/autocomplete.vue?vue&type=template&id=70936760&\");\n/* harmony import */ var _autocomplete_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./autocomplete.vue?vue&type=script&lang=js& */ \"./assets/public/autocomplete.vue?vue&type=script&lang=js&\");\n/* empty/unused harmony star reexport *//* harmony import */ var _node_modules_vue_loader_lib_runtime_componentNormalizer_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../node_modules/vue-loader/lib/runtime/componentNormalizer.js */ \"./node_modules/vue-loader/lib/runtime/componentNormalizer.js\");\n\n\n\n\n\n/* normalize component */\n\nvar component = Object(_node_modules_vue_loader_lib_runtime_componentNormalizer_js__WEBPACK_IMPORTED_MODULE_2__[\"default\"])(\n  _autocomplete_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_1__[\"default\"],\n  _autocomplete_vue_vue_type_template_id_70936760___WEBPACK_IMPORTED_MODULE_0__[\"render\"],\n  _autocomplete_vue_vue_type_template_id_70936760___WEBPACK_IMPORTED_MODULE_0__[\"staticRenderFns\"],\n  false,\n  null,\n  null,\n  null\n  \n)\n\n/* hot reload */\nif (false) { var api; }\ncomponent.options.__file = \"assets/public/autocomplete.vue\"\n/* harmony default export */ __webpack_exports__[\"default\"] = (component.exports);\n\n//# sourceURL=webpack:///./assets/public/autocomplete.vue?");

/***/ }),

/***/ "./assets/public/autocomplete.vue?vue&type=script&lang=js&":
/*!*****************************************************************!*\
  !*** ./assets/public/autocomplete.vue?vue&type=script&lang=js& ***!
  \*****************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _node_modules_vue_loader_lib_index_js_vue_loader_options_autocomplete_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../node_modules/vue-loader/lib??vue-loader-options!./autocomplete.vue?vue&type=script&lang=js& */ \"./node_modules/vue-loader/lib/index.js?!./assets/public/autocomplete.vue?vue&type=script&lang=js&\");\n/* empty/unused harmony star reexport */ /* harmony default export */ __webpack_exports__[\"default\"] = (_node_modules_vue_loader_lib_index_js_vue_loader_options_autocomplete_vue_vue_type_script_lang_js___WEBPACK_IMPORTED_MODULE_0__[\"default\"]); \n\n//# sourceURL=webpack:///./assets/public/autocomplete.vue?");

/***/ }),

/***/ "./assets/public/autocomplete.vue?vue&type=template&id=70936760&":
/*!***********************************************************************!*\
  !*** ./assets/public/autocomplete.vue?vue&type=template&id=70936760& ***!
  \***********************************************************************/
/*! exports provided: render, staticRenderFns */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _node_modules_vue_loader_lib_loaders_templateLoader_js_vue_loader_options_node_modules_vue_loader_lib_index_js_vue_loader_options_autocomplete_vue_vue_type_template_id_70936760___WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../node_modules/vue-loader/lib/loaders/templateLoader.js??vue-loader-options!../../node_modules/vue-loader/lib??vue-loader-options!./autocomplete.vue?vue&type=template&id=70936760& */ \"./node_modules/vue-loader/lib/loaders/templateLoader.js?!./node_modules/vue-loader/lib/index.js?!./assets/public/autocomplete.vue?vue&type=template&id=70936760&\");\n/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, \"render\", function() { return _node_modules_vue_loader_lib_loaders_templateLoader_js_vue_loader_options_node_modules_vue_loader_lib_index_js_vue_loader_options_autocomplete_vue_vue_type_template_id_70936760___WEBPACK_IMPORTED_MODULE_0__[\"render\"]; });\n\n/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, \"staticRenderFns\", function() { return _node_modules_vue_loader_lib_loaders_templateLoader_js_vue_loader_options_node_modules_vue_loader_lib_index_js_vue_loader_options_autocomplete_vue_vue_type_template_id_70936760___WEBPACK_IMPORTED_MODULE_0__[\"staticRenderFns\"]; });\n\n\n\n//# sourceURL=webpack:///./assets/public/autocomplete.vue?");

/***/ }),

/***/ "./assets/public/index.js":
/*!********************************!*\
  !*** ./assets/public/index.js ***!
  \********************************/
/*! no exports provided */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! vue */ \"./node_modules/vue/dist/vue.esm.browser.js\");\n/* harmony import */ var _fortawesome_fontawesome_free_css_all_min_css__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @fortawesome/fontawesome-free/css/all.min.css */ \"./node_modules/@fortawesome/fontawesome-free/css/all.min.css\");\n/* harmony import */ var _fortawesome_fontawesome_free_css_all_min_css__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_fortawesome_fontawesome_free_css_all_min_css__WEBPACK_IMPORTED_MODULE_1__);\n/* harmony import */ var _fortawesome_fontawesome_free_css_fontawesome_min_css__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @fortawesome/fontawesome-free/css/fontawesome.min.css */ \"./node_modules/@fortawesome/fontawesome-free/css/fontawesome.min.css\");\n/* harmony import */ var _fortawesome_fontawesome_free_css_fontawesome_min_css__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_fortawesome_fontawesome_free_css_fontawesome_min_css__WEBPACK_IMPORTED_MODULE_2__);\n/* harmony import */ var _app__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./app */ \"./assets/public/app.js\");\n/* harmony import */ var _styles_scss__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./styles.scss */ \"./assets/public/styles.scss\");\n/* harmony import */ var _styles_scss__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(_styles_scss__WEBPACK_IMPORTED_MODULE_4__);\n/* harmony import */ var _player_vue__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./player.vue */ \"./assets/public/player.vue\");\n/* harmony import */ var _autocomplete_vue__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./autocomplete.vue */ \"./assets/public/autocomplete.vue\");\n/**\n * This module includes code available for both the public website and\n * administration interface)\n */\n//-- vendor\n\n\n\n\n\n\n//-- aircox\n\n\n\n\n\n\n\nvue__WEBPACK_IMPORTED_MODULE_0__[\"default\"].component('a-player', _player_vue__WEBPACK_IMPORTED_MODULE_5__[\"default\"])\nvue__WEBPACK_IMPORTED_MODULE_0__[\"default\"].component('a-autocomplete', _autocomplete_vue__WEBPACK_IMPORTED_MODULE_6__[\"default\"])\n\n\nwindow.aircox = {\n    // main application\n    app: null,\n\n    // main application config\n    appConfig: {},\n\n    // player application\n    playerApp: null,\n\n    // player component\n    get player() {\n        return this.playerApp && this.playerApp.$refs.player\n    }\n};\n\n\nObject(_app__WEBPACK_IMPORTED_MODULE_3__[\"loadApp\"])({el: '#player'}).then(app => { window.aircox.playerApp = app },\n                              () => undefined)\nObject(_app__WEBPACK_IMPORTED_MODULE_3__[\"loadApp\"])(() => window.aircox.appConfig ).then(app => { window.aircox.app = app },\n                                             () => undefined)\n\n\n\n\n//# sourceURL=webpack:///./assets/public/index.js?");

/***/ }),

/***/ "./assets/public/liveInfo.js":
/*!***********************************!*\
  !*** ./assets/public/liveInfo.js ***!
  \***********************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var public_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! public/utils */ \"./assets/public/utils.js\");\n\n\n\n/* harmony default export */ __webpack_exports__[\"default\"] = (class {\n    constructor(url, timeout) {\n        this.url = url;\n        this.timeout = timeout;\n        this.promise = null;\n        this.items = [];\n    }\n\n    drop() {\n        this.promise = null;\n    }\n\n    fetch() {\n        const promise = fetch(this.url).then(response =>\n            response.ok ? response.json()\n                        : Promise.reject(response)\n        ).then(data => {\n            this.items = data;\n            return this.items\n        })\n\n        this.promise = promise;\n        return promise;\n    }\n\n    refresh() {\n        const promise = this.fetch();\n        promise.then(data => {\n            if(promise != this.promise)\n                return [];\n\n            Object(public_utils__WEBPACK_IMPORTED_MODULE_0__[\"setEcoTimeout\"])(() => this.refresh(), this.timeout*1000)\n        })\n        return promise\n    }\n});\n\n\n//# sourceURL=webpack:///./assets/public/liveInfo.js?");

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

/***/ "./assets/public/utils.js":
/*!********************************!*\
  !*** ./assets/public/utils.js ***!
  \********************************/
/*! exports provided: setEcoTimeout, setEcoInterval */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"setEcoTimeout\", function() { return setEcoTimeout; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"setEcoInterval\", function() { return setEcoInterval; });\n\n\nfunction setEcoTimeout(func, ...args) {\n    return setTimeout((...args) => {\n        !document.hidden && func(...args)\n    }, ...args)\n}\n\n\nfunction setEcoInterval(func, ...args) {\n    return setInterval((...args) => {\n        !document.hidden && func(...args)\n    }, ...args)\n}\n\n\n\n//# sourceURL=webpack:///./assets/public/utils.js?");

/***/ }),

/***/ "./node_modules/vue-loader/lib/index.js?!./assets/admin/statistics.vue?vue&type=script&lang=js&":
/*!****************************************************************************************************************!*\
  !*** ./node_modules/vue-loader/lib??vue-loader-options!./assets/admin/statistics.vue?vue&type=script&lang=js& ***!
  \****************************************************************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n//\n//\n//\n//\n//\n//\n\n\nconst splitReg = new RegExp(`,\\s*`, 'g');\n\n/* harmony default export */ __webpack_exports__[\"default\"] = ({\n    data() {\n        return {\n            counts: {},\n        }\n    },\n\n    methods: {\n        update() {\n            const items = this.$el.querySelectorAll('input[name=\"data\"]:checked')\n            const counts = {};\n\n            console.log(items)\n            for(var item of items)\n                if(item.value)\n                    for(var tag of item.value.split(splitReg))\n                        counts[tag.trim()] = (counts[tag.trim()] || 0) + 1;\n            this.counts = counts;\n        },\n\n        onclick(event) {\n            // TODO: row click => check checkbox\n        }\n    },\n\n    mounted() {\n        this.$refs.form.addEventListener('change', () => this.update())\n        this.update()\n    }\n});\n\n\n//# sourceURL=webpack:///./assets/admin/statistics.vue?./node_modules/vue-loader/lib??vue-loader-options");

/***/ }),

/***/ "./node_modules/vue-loader/lib/index.js?!./assets/public/autocomplete.vue?vue&type=script&lang=js&":
/*!*******************************************************************************************************************!*\
  !*** ./node_modules/vue-loader/lib??vue-loader-options!./assets/public/autocomplete.vue?vue&type=script&lang=js& ***!
  \*******************************************************************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var lodash_debounce__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! lodash/debounce */ \"./node_modules/lodash/debounce.js\");\n/* harmony import */ var lodash_debounce__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(lodash_debounce__WEBPACK_IMPORTED_MODULE_0__);\n/* harmony import */ var buefy_dist_components_autocomplete__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! buefy/dist/components/autocomplete */ \"./node_modules/buefy/dist/components/autocomplete/index.js\");\n/* harmony import */ var buefy_dist_components_autocomplete__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(buefy_dist_components_autocomplete__WEBPACK_IMPORTED_MODULE_1__);\n/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! vue */ \"./node_modules/vue/dist/vue.esm.browser.js\");\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n//\n\n\n\n\n\n/* harmony default export */ __webpack_exports__[\"default\"] = ({\n    props: {\n        url: String,\n        model: Function,\n        placeholder: String,\n        field: {type: String, default: 'value'},\n        count: {type: Number, count: 10},\n        valueAttr: String,\n        valueField: String,\n    },\n\n    data() {\n        return {\n            data: [],\n            selected: null,\n            isFetching: false,\n        };\n    },\n\n    methods: {\n        onSelect(option) {\n            console.log('selected', option)\n            vue__WEBPACK_IMPORTED_MODULE_2__[\"default\"].set(this, 'selected', option);\n            this.$emit('select', option);\n        },\n\n        fetch: lodash_debounce__WEBPACK_IMPORTED_MODULE_0___default()(function(query) {\n            if(!query)\n                return;\n\n            this.isFetching = true;\n            this.model.fetchAll(this.url.replace('${query}', query))\n                .then(data => {\n                    this.data = data;\n                    this.isFetching = false;\n                }, data => { this.isFetching = false; Promise.reject(data) })\n        }),\n    },\n\n    components: {\n        Autocomplete: buefy_dist_components_autocomplete__WEBPACK_IMPORTED_MODULE_1__[\"Autocomplete\"],\n    },\n});\n\n\n\n//# sourceURL=webpack:///./assets/public/autocomplete.vue?./node_modules/vue-loader/lib??vue-loader-options");

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

/***/ "./node_modules/vue-loader/lib/loaders/templateLoader.js?!./node_modules/vue-loader/lib/index.js?!./assets/admin/statistics.vue?vue&type=template&id=47005a51&":
/*!**************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/vue-loader/lib/loaders/templateLoader.js??vue-loader-options!./node_modules/vue-loader/lib??vue-loader-options!./assets/admin/statistics.vue?vue&type=template&id=47005a51& ***!
  \**************************************************************************************************************************************************************************************************/
/*! exports provided: render, staticRenderFns */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"render\", function() { return render; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"staticRenderFns\", function() { return staticRenderFns; });\nvar render = function() {\n  var _vm = this\n  var _h = _vm.$createElement\n  var _c = _vm._self._c || _h\n  return _c(\n    \"form\",\n    { ref: \"form\" },\n    [_vm._t(\"default\", null, { counts: _vm.counts })],\n    2\n  )\n}\nvar staticRenderFns = []\nrender._withStripped = true\n\n\n\n//# sourceURL=webpack:///./assets/admin/statistics.vue?./node_modules/vue-loader/lib/loaders/templateLoader.js??vue-loader-options!./node_modules/vue-loader/lib??vue-loader-options");

/***/ }),

/***/ "./node_modules/vue-loader/lib/loaders/templateLoader.js?!./node_modules/vue-loader/lib/index.js?!./assets/public/autocomplete.vue?vue&type=template&id=70936760&":
/*!*****************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/vue-loader/lib/loaders/templateLoader.js??vue-loader-options!./node_modules/vue-loader/lib??vue-loader-options!./assets/public/autocomplete.vue?vue&type=template&id=70936760& ***!
  \*****************************************************************************************************************************************************************************************************/
/*! exports provided: render, staticRenderFns */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"render\", function() { return render; });\n/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, \"staticRenderFns\", function() { return staticRenderFns; });\nvar render = function() {\n  var _vm = this\n  var _h = _vm.$createElement\n  var _c = _vm._self._c || _h\n  return _c(\n    \"div\",\n    { staticClass: \"control\" },\n    [\n      _c(\"Autocomplete\", {\n        ref: \"autocomplete\",\n        attrs: {\n          data: _vm.data,\n          placeholder: _vm.placeholder,\n          field: _vm.field,\n          loading: _vm.isFetching,\n          \"open-on-focus\": \"\"\n        },\n        on: {\n          typing: _vm.fetch,\n          select: function(object) {\n            return _vm.onSelect(object)\n          }\n        }\n      }),\n      _vm._v(\" \"),\n      _vm.valueField\n        ? _c(\"input\", {\n            ref: \"value\",\n            attrs: { type: \"hidden\", name: _vm.valueField },\n            domProps: {\n              value:\n                _vm.selected && _vm.selected[_vm.valueAttr || _vm.valueField]\n            }\n          })\n        : _vm._e()\n    ],\n    1\n  )\n}\nvar staticRenderFns = []\nrender._withStripped = true\n\n\n\n//# sourceURL=webpack:///./assets/public/autocomplete.vue?./node_modules/vue-loader/lib/loaders/templateLoader.js??vue-loader-options!./node_modules/vue-loader/lib??vue-loader-options");

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