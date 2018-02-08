
scroll_margin = 0
window.addEventListener('scroll', function(e) {
    if(window.scrollX > scroll_margin)
        document.body.setAttribute('scrollX', 1)
    else
        document.body.removeAttribute('scrollX')

    if(window.scrollY > scroll_margin)
        document.body.setAttribute('scrollY', 1)
    else
        document.body.removeAttribute('scrollY')
});



/// TODO: later get rid of it in order to use Vue stuff
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





