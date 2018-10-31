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
        new_page = "login-page";
        p = document.getElementById("login-page");
        p.style.display = "block";
    }

    if (new_page == "login-page")
    {
        document.getElementById("username").focus();
    }
    else if (new_page == "otpcode-page")
    {
        document.getElementById("otpcode").focus();
    }
}

/** Shortcut function to switch back to the login page */
function reset_login_page(){
    json_login_data["otpcode"] = null;
    show_page("login-page");
}

/** Function to reset the progress page and bar back to defaults */
function reset_progress_page(){
    var bar = document.getElementById("login-bar")
    bar.style.width = "0%";
    bar.className = "login-bar";
    bar.innerHTML = "0%";

    var para = document.getElementById("login-text");
    para.className = "login-text";
    para.textContent = "Waiting...";

    var button = document.getElementById("login_submit_button");
    button.textContent = "CANCEL";
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
    reset_progress_page();
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
        <div id="login-progress" class="login-progress">\
            <div id="login-bar" class="login-bar"></div>\
          </div>\
          <button id="login_submit_button", class="contact-form__button" \
                  type="submit">Cancel</button>\
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
    var width = value;
    if (width < start){
        width = start;
    }
    else if (width > 100){
        width = 100;
    }

    elem.style.width = width + '%';
    elem.innerHTML = width * 1 + '%';
}

/** Sets the progress bar to show failure */
function login_failure(message){
    var bar = document.getElementById("login-bar")
    bar.style.width = "100%";
    bar.className = "login-bar-failure";
    bar.innerHTML = "FAILED LOGIN";

    var para = document.getElementById("login-text");
    para.className = "login-text-failure";
    para.textContent = message;

    var button = document.getElementById("login_submit_button");
    button.textContent = "TRY AGAIN";
}

/** This function is used to submit the login data to the server,
 *  without first showing testing data
 */
function perform_login_submit(){

    set_progress(0, 0, "Starting login...");
    show_page("progress-page");

    function result_success(message){
        set_progress(100, 100, `Successfully logged in: ${message}`);
    }

    function interpret_result(result_json){
        set_progress(80, 90, "Interpreting result...");
        console.log(result_json);

        var response = null;

        try{
            response = JSON.parse(result_json);
        } catch(e){
            login_failure("Cannot decode server result: ${e}");
            return;
        }

        if (response["status"] != 0)
        {
            login_failure(response["message"]);
            return;
        }
        else
        {
            result_success(response["message"]);
        }
    }

    function decrypt_result(result_json, keyPair){
        set_progress(60, 80, "Decrypting result...");
        console.log(result_json);
        console.log(keyPair.privateKey);
        interpret_result(result_json);
    }

    function fetch_server(encrypted_json, keyPair){
        set_progress(30, 60, "Sending login data to server...");
        console.log(encrypted_json);
        fetch(identity_service_url, {
            method: 'post',
            headers: {
                'Accept': 'application/json, test/plain, */*',
                'Content-Type': 'application/json'
            },
            body: encrypted_json
        })
        .then((response) => {
            response.json().then((response) => {
                decrypt_result(response, keyPair);
            })
            .catch((err) => {
                console.log(`Failed to get json from ${response.status} ${response.text()}`);
                login_failure(`Failed to decode response ${response} : ${err}`);
            })
        })
        .catch((err) => {
            console.log(`Failed to connect to ${identity_service_url}`);
            console.log(err);
            login_failure(`Failed to connect! ${err}`);
        })
    }

    function encrypt_json(args_json){
        set_progress(0, 30, "Encrypting login info...");
        const crypto = new OpenCrypto();

        //first generate a key-pair that will be used to
        //decrypt the result back from the server...
        crypto.getKeyPair()
        .then((keyPair) => {
            //now convert the pem public key to a crypto key
            crypto.pemPublicToCrypto(getIdentityPublicPem())
            .then((pubkey) => {
                crypto.encryptPublic(pubkey, args_json)
                .then((encrypted_json) => {
                    var data = {};
                    data["data"] = bytes_to_string(encrypted_json);
                    data["encrypted"] = true;
                    console.log(data);
                    fetch_server(JSON.stringify(data), keyPair);
                })
                .catch((err) =>{
                    console.log("Could not encrypt the arguments?");
                    console.log(err);
                    login_failure(`Could not encrypt data: ${err}`);
                })
            })
            .catch((err) => {
                console.log("Couldn't import the server's public key?");
                console.log(err);
                login_failure(`Could not import the server's public key: ${err}`);
            })
        })
        .catch((err) => {
            console.log("Couldn't generate a public/private key pair?");
            console.log(err);
            login_failure(`Could not generate a key pair: ${err}`);
        });
    }

    var server_public_key = "PUBLIC KEY INSERTED INTO DOCUMENT BY SERVER";
    encrypt_json(JSON.stringify(json_login_data));

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
