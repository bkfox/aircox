

export function setEcoTimeout(func, ...args) {
    return setTimeout((...args) => {
        !document.hidden && func(...args)
    }, ...args)
}


export function setEcoInterval(func, ...args) {
    return setInterval((...args) => {
        !document.hidden && func(...args)
    }, ...args)
}

