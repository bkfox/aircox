
/// Helper to provide a tab+panel functionnality; the tab and the selected
/// element will have an attribute "selected".
/// We assume a common ancestor between tab and panel at a maximum level
/// of 2.
/// * tab: corresponding tab
/// * panel_selector is used to select the right panel object.
function select_tab(tab, panel_selector) {
    var parent = tab.parentNode.parentNode;
    var panel = parent.querySelector(panel_selector);

    // unselect
    var qs = parent.querySelectorAll('*[selected]');
    for(var i = 0; i < qs.length; i++)
        if(qs[i] != tab && qs[i] != panel)
            qs[i].removeAttribute('selected');

    panel.setAttribute('selected', 'true');
    tab.setAttribute('selected', 'true');
}


/// Utility to store objects in local storage. Data are stringified in JSON
/// format in order to keep type.
function Store(prefix) {
    this.prefix = prefix;
}

Store.prototype = {
    // save data to localstorage, or remove it if data is null
    set: function(key, data) {
        key = this.prefix + '.' + key;
        if(data == undefined) {
            localStorage.removeItem(prefix);
            return;
        }
        localStorage.setItem(key, JSON.stringify(data))
    },

    // load data from localstorage
    get: function(key) {
        try {
            key = this.prefix + '.' + key;
            var data = localStorage.getItem(key);
            if(data)
                return JSON.parse(data);
        }
        catch(e) { console.log(e, data); }
    },

    // return true if the given item is stored
    exists: function(key) {
        key = this.prefix + '.' + key;
        return (localStorage.getItem(key) != null);
    },

    // update a field in the stored data
    update: function(key, field_key, value) {
        data = this.get(key) || {};
        if(value)
            data[field_key] = value;
        else
            delete data[field_key];
        this.set(key, data);
    },
}


