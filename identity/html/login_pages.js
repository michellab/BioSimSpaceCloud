/**
 *  These are the functions that render individual pages / views
 *  for the login application
 */
function render_main(){
    document.write(
        '<h1 class="content__heading">\
            <a href="' + getIdentityServiceURL() + '">\
                Logging into Acquire\
            </a>\
        </h1>\
        <p class="content__lede">\
        (unique session ID ' + getSessionUID() + ')\
        </p>\
        <form class="content__form contact-form">\
        <div class="contact-form__input-group">\
            <label class="contact-form__label" for="username">username</label>\
            <input class="contact-form__input contact-form__input--text"\
                id="username" name="username"\
                type="text" autofill="username"/>\
        </div>\
        <div class="contact-form__input-group">\
            <label class="contact-form__label" for="password">password</label>\
            <input class="contact-form__input contact-form__input--text"\
                id="password" name="password" type="password"\
                autofill="password"/>\
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
        <input name="function" type="hidden" value="login"/>\
        <input name="short_uid" type="hidden" value="' +
                   getSessionUID() + '"/>');

    var device_uid = getDeviceUID();
    if (device_uid){
        document.write("<input name='device_uid' type='hidden' value='" +
                       device_uid + "'/>")
    }
    document.write('</form>');

    if (isTesting()){
        document.write(
          '<div class="results">\
            <h2 class="results__heading">Form Data</h2>\
            <pre class="results__display-wrapper"><code class="results__display"></code></pre>\
          </div>');
    }

    /**
     * A handler function to prevent default submission and run our custom script.
     * @param  {Event} event  the submit event triggered by the user
     * @return {void}
    */
    var handleFormSubmit = function handleFormSubmit(event) {
        // Stop the form from submitting since we’re handling that with AJAX.
        event.preventDefault();

        // Call our function to get the form data.
        var data = formToJSON(form.elements);

        var all_ok = 1;
        var remind_username = 0;
        var remind_password = 0;
        var remember_username = null;

        // make sure that we have everything we need...
        if (!data["username"]){
            remind_username = 1;
            all_ok = 0;
        }
        else{
            remember_username = data["username"];
        }

        if (!data["password"]){
            remind_password = 1;
            all_ok = 0;
        }

        if (!all_ok)
        {
            return;
        }

        // Testing only: print the form data onscreen as a formatted JSON object.
        if (isTesting()){
            var dataContainer = document.getElementsByClassName('results__display')[0];

            // Use `JSON.stringify()` to make the output valid, human-readable JSON.
            dataContainer.textContent = JSON.stringify(data, null, "  ");
        }

        // ...this is where we’d actually do something with the form data...
        // I WANT TO ENCRYPT THE JSON AND SEND IT AS A POST TO THE IDENTITY SERVER
        var server_public_key = "PUBLIC KEY INSERTED INTO DOCUMENT BY SERVER";
        var args_json = JSON.stringify(data);
        //var encrypted_json = server_public_key.encrypt(args_json);

        // now generate a new pub/priv keypair to encrypt the server call...

        // now call the service by posing the encrypted_json and waiting for
        // the result...
        console.log(identity_service_url);
        console.log(args_json);

        /*fetch(identity_service_url)
        .then(function(response) {
            return response.json();
        })
        .then(function(myJson) {
            console.log(JSON.stringify(myJson));
        });*/

        // if remember_device then encrypt the returned otpsecret using the
        // user's password (we need a secret to keep it safe in the cookiestore)

        // now tell the user whether or not they were successful, and that they
        // can now close this window (or click a link to try again)
    };

    var form = document.getElementsByClassName('contact-form')[0];
    form.addEventListener('submit', handleFormSubmit);
}
