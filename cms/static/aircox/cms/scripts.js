

/// Small utility used to make XMLHttpRequests, and map results on objects.
/// This is intended to dynamically retrieve Section and exposed data.
///
/// Request.Selector is a utility class that can be used to map data using
/// selectors.
///
/// Since there is no a common method to render items in JS and Django, we
/// retrieve items yet rendered, and select data over it.
function Request_(url = '', params = '') {
  this.url = url;
  this.params = params;
  this.selectors = [];
  this.actions = [];
}

Request_.prototype = {
  /// XMLHttpRequest object used to retrieve data
  xhr: null,

  /// delayed actions that have been registered
  actions: null,

  /// registered selectors
  selectors: null,

  /// parse request result and save in this.stanza
  __parse_dom: function() {
    if(self.stanza)
      return;

    var doc = document.implementation.createHTMLDocument('xhr').documentElement;
    doc.innerHTML = this.xhr.responseText;
    this.stanza = doc;
  },

  /// make an xhr request, and call callback(err, xhr) if given
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

  /// send request
  send: function() {
    this.xhr.send();
    return this;
  },

  /// set selectors.
  /// * callback: if set, call it once data are downloaded with an object
  ///   of elements matched with the given selectors only. The object is
  ///   made of `selector_name: select_result` items.
  select: function(selectors, callback = undefined) {
    for(var i in selectors) {
      selector = selectors[i];
      if(!selector.sort)
        selector = [selector]

      selector = new Request_.Selector(i, selector[0], selector[1], selector[2])
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

  /// map data using this.selectors on xhr result *and* dest
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

  /// add an action to the list of actions
  on: function(callback) {
    this.actions.push(callback)
    return this;
  },
};


Request_.Selector = function(name, selector, attribute = null, all = false) {
  this.name = name;
  this.selector = selector;
  this.attribute = attribute;
  this.all = all;
}

Request_.Selector.prototype = {
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
        dst[this.attribute] = src[this.attribute] || '';
      else
        dst.parentNode.replaceChild(src, dst);
    }
  },
}


/// Just to by keep same convention between utilities
/// Create an instance of Request_
function Request(url = '', params = '') {
  return new Request_(url, params);
}


var Section = {
    /// Return the parent section of a DOM element. Compare it using its
    /// className. If not class_name is given, use "section"
    get_section: function(item, class_name) {
        class_name = class_name || 'section';
        while(item) {
            if(item.className && item.className.indexOf(class_name) != -1)
                break
            item = item.parentNode;
        }
        return item;
    },


    /// Load a section using the given url and parameters, update the header,
    /// the content and the footer automatically. No need to add "embed" in
    /// url params.
    ///
    /// If find_section is true, item is a child of the wanted section.
    ///
    /// Return a Request.Selector
    load: function(item, url, params, find_section) {
        if(find_section)
            item = this.get_section(item);

        var rq = Request(url, 'embed&' + (params || ''))
        return rq.get().select({
            'header': ['header', 'innerHTML', true],
            'content': ['.content', 'innerHTML', true],
            'footer': ['footer', 'innerHTML', true]
        }).map(item).send();
    },


    /// Load a Section on event, and handle it.
    load_event: function(event, params) {
        var item = event.currentTarget;
        var url = item.getAttribute('href');

        event.preventDefault();

        this.load(item, url, params, true);
        return true;
    },
}




