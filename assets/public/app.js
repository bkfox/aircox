import Vue from 'vue';


export var app = null;
export default app;

function loadApp() {
    app = new Vue({
      el: '#app',
      delimiters: [ '[[', ']]' ],
    })
}

window.addEventListener('load', loadApp);



