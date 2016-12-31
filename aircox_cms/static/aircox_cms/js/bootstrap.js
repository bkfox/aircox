
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


