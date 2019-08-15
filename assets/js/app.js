import Vue from 'vue';
import Buefy from 'buefy';

Vue.use(Buefy);

export var app = null;

function loadApp() {
    app = new Vue({
      el: '#app',
      delimiters: [ '[[', ']]' ],
    })
}


window.addEventListener('load', loadApp);


