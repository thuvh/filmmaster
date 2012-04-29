{% load json %}
if(!window.console) {
    console = new function() {
        this.log = this.debug = this.info = function() {}
    }
}

window.settings = {{global.js_data|json|default:"{}"}};
