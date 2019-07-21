import Vue from 'vue';
import Buefy from 'buefy';

Vue.use(Buefy);

window.addEventListener('load', () => {
    var app = new Vue({
      el: '#app',
      delimiters: [ '[[', ']]' ],
    })
});



