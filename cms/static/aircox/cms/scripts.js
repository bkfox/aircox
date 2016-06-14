
function Part(url = '', params = '') {
  return new Part_(url, params);
}

// Small utility used to make XMLHttpRequests, and map results to other
// objects
function Part_(url = '', params = '') {
  this.url = url;
  this.params = params;
  this.selectors = [];
  this.actions = [];
}

Part_.prototype = {
  // XMLHttpRequest object used to retrieve data
  xhr: null,

  // delayed actions that have been registered
  actions: null,

  // registered selectors
  selectors: null,

  /// parse request result and save in this.stanza
  __parse_dom: function() {
    if(self.stanza)
      return;

    var doc = document.implementation.createHTMLDocument('xhr').documentElement;
    doc.innerHTML = this.xhr.responseText;
    this.stanza = doc;
  },

  // make an xhr request, and call callback(err, xhr) if given
  get: function() {
    var self = this;

    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
      if(xhr.readyState != 4)
        return

      // TODO: error handling
      var err = self.xhr.status != 200 && self.xhr.status;
      if(err)
        return;

      for(var i = 0; i < self.actions.length; i++)
        self.actions[i].apply(self);
    }

    if(this.params)
      xhr.open('GET', this.url + '?' + this.params, true);
    else
      xhr.open('GET', this.url, true);
    this.xhr = xhr;
    return this;
  },

  // send request
  send: function() {
    this.xhr.send();
    return this;
  },

  // set selectors.
  // * callback: if set, call it once data are downloaded with an object
  //   of elements matched with the given selectors only. The object is
  //   made of `selector_name: select_result` items.
  select: function(selectors, callback = undefined) {
    for(var i in selectors) {
      selector = selectors[i];
      if(!selector.sort)
        selector = [selector]

      selector = new Part_.Selector(i, selector[0], selector[1], selector[2])
      selectors[i] = selector;
      this.selectors.push(selector)
    }

    if(callback) {
      var self = this;
      this.actions.push(function() {
        self.__parse_dom();

        var r = {}
        for(var i in selectors) {
          r[i] = selectors[i].select(self.stanza);
        }
        callback(r);
      });
    }
    return this;
  },

  // map data using this.selectors on xhr result *and* dest
  map: function(dest) {
    var self = this;
    this.actions.push(function() {
      self.__parse_dom();

      for(var i = 0; i < self.selectors.length; i++) {
        selector = self.selectors[i]
        selector.map(self.stanza, dest);
      }
    });
    return this;
  },

  // add an action to the list of actions
  on: function(callback) {
    this.actions.push(callback)
    return this;
  },
};


Part_.Selector = function(name, selector, attribute = null, all = false) {
  this.name = name;
  this.selector = selector;
  this.attribute = attribute;
  this.all = all;
}

Part_.Selector.prototype = {
  select: function(obj, use_attr = true) {
    if(!this.all) {
      obj = obj.querySelector(this.selector)
      return (this.attribute && use_attr && obj) ? obj[this.attribute] : obj;
    }

    obj = obj.querySelectorAll(this.selector);
    if(!obj)
      return;

    r = []
    for(var i = 0; i < obj.length; i++) {
      r.push(this.attribute && use_attr ? obj[i][this.attribute] : obj[i])
    }
    return r;
  },

  map: function(src, dst) {
    src_qs = this.select(src, false);
    dst_qs = this.select(dst, false);
    if(!src_qs || !dst_qs)
      return

    if(!this.all) {
      src_qs = [ src_qs ];
      dst_qs = [ dst_qs ];
    }

    var size = Math.min(src_qs.length, dst_qs.length);
    for(var i = 0; i < size; i++) {
      var src = src_qs[i];
      var dst = dst_qs[i];

      if(this.attribute)
        dst[this.attribute] = src[this.attribute];
      else
        dst.parentNode.replaceChild(src, dst);
    }
  },
}


