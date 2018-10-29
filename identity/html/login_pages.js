/**
 *  These are the functions that render individual pages / views
 *  for the login application
 */

var json_login_data = {};

var pages = ["login-page", "otpcode-page", "progress-page", "test-page"];

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
function reset_login_page(){
    json_login_data["otpcode"] = null;
    show_page("login-page");
}

/** This function renders the test page */
function render_test_page(){
    document.write(
        '<h1 class="content__heading">\
            <a href="' + getIdentityServiceURL() + '">\
                Logging into Acquire\
            </a>\
         </h1>\
         <p class="content__lede">\
         (unique session ID ' + getSessionUID() + ')\
         </p>\
         <form class="content__form contact-form" id="login-progress-form">\
         <label class="contact-form__label">\
          JSON data to be submitted to server...\
         </label>\
         <pre class="results__display-wrapper"><code class="results__display"></code></pre>\
         <button type="button" class="contact-form__button" onclick="reset_login_page()">Back</button>\
         <button type="button" class="contact-form__button" onclick="perform_login_submit()">Submit</button>\
         </form>');
}

/** This function cancels a login request */
function cancel_login(){
    reset_login_page();
}

/** This function renders the progress page */
function render_progress_page(){
    document.write(
        '<h1 class="content__heading">\
            <a href="' + getIdentityServiceURL() + '">\
                Logging into Acquire\
            </a>\
        </h1>\
        <p class="content__lede">\
        (unique session ID ' + getSessionUID() + ')\
        </p>\
        <form class="content__form contact-form" id="login-progress-form">\
        <label class="contact-form__label" id="login-text">\
        Collecting data...\
        </label>\
        <div id="login-progress">\
            <div id="login-bar"></div>\
          </div>\
          <button class="contact-form__button" type="submit">Cancel</button>\
          </form>'
    );

    /**
     * A handler function to prevent default submission and run our custom script.
     * @param  {Event} event  the submit event triggered by the user
     * @return {void}
    */
    var handleFormSubmit = function handleFormSubmit(event) {
        // Stop the form from submitting since we’re handling that with AJAX.
        event.preventDefault();
        cancel_login();
    };

    var form = document.getElementById('login-progress-form');
    form.addEventListener('submit', handleFormSubmit);
}

/** This function is used to get the otpcode from either the user
 *  of from secure storage
 */
function get_otpcode(){

    //can't get the otpcode from local storage so have to ask
    //the user to supply it
    if (!json_login_data["otpcode"]){
        show_page("otpcode-page");
        return;
    }

    perform_login();
}

/** Function to update the progress bar */
function set_progress(start, value, text) {
    var para = document.getElementById("login-text");
    para.textContent = text;
    var elem = document.getElementById("login-bar");
    var width = start;
    var id = setInterval(frame, 10);
    function frame() {
        if (width >= value) {
            clearInterval(id);
        } else if (width >= 100){
            clearInterval(id);
        }
        else {
            width++;
            elem.style.width = width + '%';
            elem.innerHTML = width * 1 + '%';
        }
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

/** This function is used to submit the login data to the server,
 *  without first showing testing data
 */
function perform_login_submit(){

    set_progress(0, 0, "Starting login...");
    show_page("progress-page");

    // ...this is where we’d actually do something with the form data...
    // I WANT TO ENCRYPT THE JSON AND SEND IT AS A POST TO THE IDENTITY SERVER
    var server_public_key = "PUBLIC KEY INSERTED INTO DOCUMENT BY SERVER";
    var args_json = JSON.stringify(json_login_data);
    //var encrypted_json = server_public_key.encrypt(args_json);

    set_progress(0, 30, "Encrypting login info...");

    var id = setInterval(frame, 1000);
    var i = 0;
    function frame() {
        if (i == 0){
            set_progress(30, 60, "Transmitting login details to server...");
            i += 1;
        }
        else if (i == 1){
            set_progress(60, 100, "Decoding result...");
            i += 1;
        }
        else
        {
            set_progress(100, 100, "Successfully logged in");
            clearInterval(id);
        }
    }

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

}

/** This function is used to submit the login data to the server */
function perform_login(){

    // Testing only: print the form data onscreen as a formatted JSON object.
    if (isTesting()){
        var dataContainer = document.getElementsByClassName('results__display')[0];

        // Use `JSON.stringify()` to make the output valid, human-readable JSON.
        dataContainer.textContent = JSON.stringify(json_login_data, null, "  ");

        show_page("test-page");
        return;
    }

    perform_login_submit();
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
        <form class="content__form contact-form" id="user-login-form">\
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
            json_login_data["password"] = data["password"];
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

        // now try to get the one-time-code - this will move onto the
        // next stage of the process...
        get_otpcode();
    };

    var form = document.getElementById('user-login-form');
    form.addEventListener('submit', handleFormSubmit);
}

/** This function renders the device page */
function render_otpcode_page()
{
    document.write(
        '<h1 class="content__heading">\
            <a href="' + getIdentityServiceURL() + '">\
                Logging into Acquire\
            </a>\
        </h1>\
        <p class="content__lede">\
        (unique session ID ' + getSessionUID() + ')\
        </p>\
        <form class="content__form contact-form" id="user-otpcode-form">\
        <div class="contact-form__input-group">\
            <label class="contact-form__label" for="otpcode">\
            2-step Verification - \
            Get a verification code from your Authenticator app \
              <span class="contact-form__remind-input" id="contact-form__remind-otpcode"> (*) you must supply a 2-step verification code</span>\
              </label>\
            <input class="contact-form__input contact-form__input--text"\
                id="otpcode" name="otpcode"\
                type="text"/>\
        </div>\
        <div class="contact-form__input-group">\
            <p class="contact-form__label--checkbox-group">Remember device</p>\
            <input class="contact-form__input contact-form__input--checkbox"\
                id="remember_device" name="remember_device" type="checkbox"\
                value="true"/>\
        </div>\
        <button class="contact-form__button" type="submit">Login</button>\
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
        if (data["otpcode"]){
            json_login_data["otpcode"] = data["otpcode"];
            var remind_input = document.getElementById("contact-form__remind-otpcode");
            remind_input.style.display = "none";
        }
        else{
            var remind_input = document.getElementById("contact-form__remind-otpcode");
            remind_input.style.display = "inline";
            all_ok = 0;
        }

        json_login_data["remember_device"] = data["remember_device"];

        if (all_ok)
        {
            perform_login();
        }
    };

    var form = document.getElementById('user-otpcode-form');
    form.addEventListener('submit', handleFormSubmit);
}
