/**
 *  These are the functions that render individual pages / views
 *  for the login application
 */

var json_login_data = {};

var pages = ["login-page", "otp-page", "progress-page", "test-page"];

/** Function used to switch views between different pages */
function show_page(new_page){
    selected = null;

    pages.forEach((page) => {
        p = document.getElementById(page);

        if (new_page == page){
            p.style.display = "block";
            selected = page;
        }
        else{
            p.style.display = "none";
        }
    });

    if (!selected){
        p = document.getElementById("login-page");
        p.style.display = "block";
    }
}

/** Shortcut function to switch back to the login page */
function show_login_page(){
    show_page("login-page");
}

/** This function renders the test page */
function render_test_page(){
    document.write(
        '<div class="results">\
          <h2 class="results__heading">Form Data</h2>\
          <pre class="results__display-wrapper"><code class="results__display"></code></pre>\
          <button type="button" onclick="show_login_page()">Back</button>\
          <button type="button" onclick="perform_login()">Submit</button>\
          </div>');
}

/** This function is used to get the otpcode from either the user
 *  of from secure storage
 */
function get_otpcode(){
    json_login_data["otpcode"] = "56789";
}

/* This function renders the login page */
function render_login_page(){
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
            <label class="contact-form__label" for="username">\
              username\
              <span class="contact-form__remind-input" id="contact-form__remind-username"> (*) you must supply a username</span>\
              </label>\
            <input class="contact-form__input contact-form__input--text"\
                id="username" name="username"\
                type="text" autofill="username"/>\
        </div>\
        <div class="contact-form__input-group">\
            <label class="contact-form__label" for="password">\
            password\
            <span class="contact-form__remind-input" id="contact-form__remind-password"> (*) you must supply a password</span>\
            </label>\
            <input class="contact-form__input contact-form__input--text"\
                id="password" name="password" type="password"\
                autofill="password"/>\
        </div>\
        <button class="contact-form__button" type="submit">Login</button>\
        <div class="contact-form__input-group">\
            <p class="contact-form__label--checkbox-group">Remember device</p>\
            <input class="contact-form__input contact-form__input--checkbox"\
                id="remember_device" name="remember_device" type="checkbox"\
                value="true"/>\
        </div>\
      </form>');

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

        // make sure that we have everything we need...
        if (data["username"]){
            json_login_data["username"] = data["username"];
            var remind_input = document.getElementById("contact-form__remind-username");
            remind_input.style.display = "none";
        }
        else{
            var remind_input = document.getElementById("contact-form__remind-username");
            remind_input.style.display = "inline";
            all_ok = 0;
        }

        if (data["password"]){
            json_login_data["password"];
            var remind_input = document.getElementById("contact-form__remind-password");
            remind_input.style.display = "none";
        }
        else{
            var remind_input = document.getElementById("contact-form__remind-password");
            remind_input.style.display = "inline";
            all_ok = 0;
        }

        if (!all_ok)
        {
            return;
        }

        json_login_data["function"] = "login";
        json_login_data["short_uid"] = getSessionUID();

        // now try to get the one-time-code
        get_otpcode();

        // Testing only: print the form data onscreen as a formatted JSON object.
        if (isTesting()){
            var dataContainer = document.getElementsByClassName('results__display')[0];

            // Use `JSON.stringify()` to make the output valid, human-readable JSON.
            dataContainer.textContent = JSON.stringify(json_login_data, null, "  ");

            show_page("test-page");
            return;
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

/** This function renders the device page */
function render_device_page()
{
    document.write('<p>Device login page</p>');
}

/** This function renders the progress page */
function render_progress_page()
{
    document.write('<p>Device progress page</p>');
}
