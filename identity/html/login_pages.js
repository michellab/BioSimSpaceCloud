/**
 *  These are the functions that render individual pages / views
 *  for the login application
 */
function render_main(){
    document.clear();

    document.write(
        '<section class="content">\
        <h1 class="content__heading">\
        <script>\
            <a href="' + getIdentityServiceURL() + '">\
        </script>Logging into Acquire</a>\
        </h1>\
        <p class="content__lede">\
        (unique session ID ' + document.write(getSessionUID()) + '</script>\
        </p>\
        <form class="content__form contact-form">\
        <div class="contact-form__input-group">\
            <label class="contact-form__label" for="username">username</label>\
            <input class="contact-form__input contact-form__input--text"\
                id="username" name="username" type="text"/>\
        </div>\
        <div class="contact-form__input-group">\
            <label class="contact-form__label" for="password">password</label>\
            <input class="contact-form__input contact-form__input--text"\
                id="password" name="password" type="password"/>\
        </div>\
        <div class="contact-form__input-group">\
            <label class="contact-form__label"\
                for="otpcode">one time authentication code</label>\
            <input class="contact-form__input contact-form__input--text"\
                id="otpcode" name="otpcode" type="text"/>\
        </div>\
        <button class="contact-form__button" type="submit">Login</button>\
        <div class="contact-form__input-group">\
            <p class="contact-form__label--checkbox-group">Remember device</p>\
            <input class="contact-form__input contact-form__input--checkbox"\
                id="remember_device" name="remember_device" type="checkbox"\
                value="true"/>\
        </div>\
        <input name="function" type="hidden" value="login"/>');

    document.write("<input name='short_uid' type='hidden' value='" +
                   getSessionUID() + "'/>");
    var device_uid = getDeviceUID();
    if (device_uid){
        document.write("<input name='device_uid' type='hidden' value='" +
                       device_uid + "'/>")
    }
    document.write(
        '</form>\
      </section>');

    if (isTesting()){
        document.write(
          "<div class=\"results\">"+
            "<h2 class=\"results__heading\">Form Data</h2>"+
            "<pre class=\"results__display-wrapper\"><code class=\"results__display\"></code></pre>"+
          "</div>");
    }

    var form = document.getElementsByClassName('contact-form')[0];
    form.addEventListener('submit', handleFormSubmit);
}
