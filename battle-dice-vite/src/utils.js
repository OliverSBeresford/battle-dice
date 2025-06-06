export const colors = [
    "#348888",
    "#22BABB",
    "#9EF8EE",
    "#FA7F08",
    "#F24405",
    "#F25EB0",
    "#B9BF04",
    "#F2B705",
    "#F27405",
    "#F23005",
];

export function get_random(list) {
    return list[Math.floor(Math.random() * list.length)];
}

export function setupGlobalErrorHandler() { 
    window.addEventListener('error', function(e) {
        const errDiv = document.createElement('div');
        errDiv.style = 'color:red;white-space:pre-wrap;';
        errDiv.textContent = 'JS Error: ' + e.message + '\n' + (e.error && e.error.stack ? e.error.stack : '');
        document.body.appendChild(errDiv);
    });
}