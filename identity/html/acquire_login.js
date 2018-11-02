/**
 *  Javascript needed to implement equivalent of acquire_login command
 *  line tool in a browser
 *
 *  Form to JSON code is inspired heavily from excellent tutorial here
 *  https://code.lengstorf.com/get-form-values-as-json/
 *
 */

/** Hard code the URL of the identity service */
var identity_service_url = "http://130.61.60.88:8080/t/identity"

/** Also hard code the data for the service's public key
 *
 *  This data is encoded using the PublicKey.to_data() function...
*/
var identity_public_pem = "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUFzR0cycjJXWXljR0t0MXEzc1hZdAprbkZaVjVSa1Z5TUV2M2VZS2o0VDExMG41b241bzBBNms1NU13cTZPVFZpUVhLVVd3enQ0K09oWDY4cXNjM2ZPCnZ2aFFZdGZpT2prcXJvNFI0djhXaXdxbjlwdmdocW04b1FmTlhqRWw1ODBvV0w4SFMzTFgvQk9TQVFyMHNpQkYKN0hMWW9QVlVrcVovdmFuUWlwWlJhNXZmTlZoNXVBcGs0b2xRRzJzL3kyZnVSZzQydEhpbldObk1YdE0wWTVGbgprV1lUK00xL3BrUDRpSVB0akg0VUg0OTQyaG5SSkRwZXArWWpJQ1g5eVZQcHRSbFhIdWYrbVVtTThNZGpHcFp1Cks3cHppTGh6L2tNNzcwejhlMEluYzEzcFNBV2VLRmRKbjFMa3F2a24vVU9XN1pMVVV6Q1VKdGZ2VjlJb0hkbVcKZ1FJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg==";
var identity_public_pem = "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUF1UXlKRmRXMFpxcWtQNlUxWEhLSwpzUGcxeFlOSXNzUm51dnZqWm81MnJzYzhlTEpjcStJNVdDRFA5c245bG9LRjhmUVI3K3JSdlBlVjczTXhnU3U1Ci9sQUVBTHU3Z0RTdWxaSExORkVGSFFOek9XUm03UEM1eU42ZTZUZWVZRkNnYzVLZWxneitRbHYvUmRaaVB2eWUKcTJtZkRvR2NhdFBEeFlEaS9sMENzMGdLNllVVWVUQXgvY01EaEQyQk1oNXhDRW5EOUNKOG0xUzFBRTNvUUlaUgpFK3JHeGtMNDJTK2taQW1HVGRNbUU2WWhNcmxEa2l5RThxR2pRUGgrdmxHRDBzaG9kODNCOTVFUmQxMmhXWlRHCkcxSE4zTWw3eXlhRlR3K0J2RE1Kc05qZGxxRTI0VllrRmpJa3JPNlJhK2UxOEQ0clNSNTNPdnc5S3dWRVYvcG8KL3dJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg==";

/** Return a fast but low quality uuid4 - this is sufficient for our uses.
 *  This code comes from
 *  https://stackoverflow.com/questions/105034/create-guid-uuid-in-javascript
 */
function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/** Get URL requestion variables as an array. This is inspired from
 *  https://html-online.com/articles/get-url-parameters-javascript/
 */
function getUrlVars() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi,
                                             function(m,key,value) {
        vars[key] = value;
    });
    return vars;
}

/** Write local data to the browser with 'name' == 'value' */
function writeData(name, value)
{
    if (typeof(Storage) !== "undefined") {
        localStorage.setItem(name, value);
    } else {
        console.log("Sorry - no web storage support. Cannot cache details!");
    }
}

/** Read local data from the browser at key 'name'. Returns
 *  NULL if no such data exists
 */
function readData(name)
{
    if (typeof(Storage) !== "undefined") {
        return localStorage.getItem(name);
    } else {
        console.log("Sorry - no web storage support. Cannot cache details!");
        return null;
    }
}

/** Get the session UID from the URL request parameters. The
 *  URL will have the form http[s]://example.com:8080/t/identity/u?id=XXXXXX
 */
function getSessionUID() {
  vars = getUrlVars();

  return session_uid = vars["id"];
}

/** Function to return whether or not we are running in testing
 *  mode - this is signified by a URL request parameter "testing"
 *  being equal to anything that is not false
 */
function isTesting(){
  vars = getUrlVars();
  return vars["testing"];
}

/** Function to return the fully qualified URL of the identity service */
function getIdentityServiceURL(){
  return identity_service_url;
}

/** Convert a string to utf-8 encoded binary bytes */
function to_utf8(s){
    var encoded = new TextEncoder("utf-8").encode(s);
    return encoded;
}

function string_to_utf8_bytes(s){
    return to_utf8(s);
}

/** Decode utf-8 encoded bytes to a string */
function from_utf8(b){
    var decoded = new TextDecoder("utf-8").decode(b);
    return decoded;
}

function utf8_bytes_to_string(b){
    return from_utf8(b);
}

/** Function to convert from a string back to binary */
function string_to_bytes(s){
    return base64js.toByteArray(s);
}

/** Function to convert binary data to a string */
function bytes_to_string(b){
    return base64js.fromByteArray(b);
}

/** Function to import a public key from the passed json data */
function getIdentityPublicPem(){
    return utf8_bytes_to_string(base64js.toByteArray(identity_public_pem));
}

/** Function to generate a public/private key pair */
async function generateKeypair(){
    return null;
    var rsa = forge.pki.rsa;
    let result = await rsa.generateKeyPair({bits: 2048, workers: -1});
    return result;
}

/** Function to load the public key of the identity service */
async function getIdentityPublicKey(){
    var pem = getIdentityPublicPem();
    console.log(pem);
    var publicKey = forge.pki.publicKeyFromPem(pem);
    return publicKey;
}

function rawBytesFromJSString( str ) {
    var ch, st, re = [], j=0;
    for (var i = 0; i < str.length; i++ ) {
        ch = str.charCodeAt(i);
        if(ch < 127)
        {
            re[j++] = ch & 0xFF;
        }
        else
        {
            st = [];    // clear stack
            do {
                st.push( ch & 0xFF );  // push byte to stack
                ch = ch >> 8;          // shift value down by 1 byte
            }
            while ( ch );
            // add stack contents to result
            // done because chars have "wrong" endianness
            st = st.reverse();
            for(var k=0;k<st.length; ++k)
                re[j++] = st[k];
        }
    }
    // return an array of bytes
    return re;
}

/** Function that encrypts the passed data with the passed public key */
async function encryptData(key, data){
    if (typeof data === 'string' || data instanceof String){
        data = string_to_utf8_bytes(data);
    }

    console.log(`INPUT = ${data}`);

    key = await key;

    var result = key.encrypt(data, 'RSA-OAEP', {
        md: forge.md.sha256.create(),
        mgf1: {
          md: forge.md.sha256.create()
        }
      });

    result = rawBytesFromJSString(result);

    console.log(`OUTPUT = ${result} | ${result.length}`);

    return result;
}

/** Function that decrypts the passed data with the passed private key */
async function decryptData(key, data){
    return key.decrypt(data, 'RSA-OAEP', {
        md: forge.md.sha256.create(),
        mgf1: {
          md: forge.md.sha256.create()
        }
      });
}

/** Function that returns the UID of this device. If this device has not
 *  been used before, then a random UID is generated and then stored to
 *  local storage. This is then re-read the next time this function is
 *  called
 */
function getDeviceUID(){
  var device_uid = readData("device_uid");
  if (device_uid){
    return device_uid;
  }
  device_uid = uuidv4();
  writeData("device_uid", device_uid);
  return device_uid;
}

/**
  * Checks that an element has a non-empty `name` and `value` property.
  * @param  {Element} element  the element to check
  * @return {Bool}             true if the element is an input, false if not
*/
var isValidElement = function isValidElement(element) {
    return element.name && element.value;
};

/**
  * Checks if an element’s value can be saved (e.g. not an unselected checkbox).
  * @param  {Element} element  the element to check
  * @return {Boolean}          true if the value should be added, false if not
*/
var isValidValue = function isValidValue(element) {
    return !['checkbox', 'radio'].includes(element.type) || element.checked;
};

/**
  * Checks if an input is a checkbox, because checkboxes allow multiple values.
  * @param  {Element} element  the element to check
  * @return {Boolean}          true if the element is a checkbox, false if not
*/
var isCheckbox = function isCheckbox(element) {
    return element.type === 'checkbox';
};

/**
  * Checks if an input is a `select` with the `multiple` attribute.
  * @param  {Element} element  the element to check
  * @return {Boolean}          true if the element is a multiselect, false if not
*/
var isMultiSelect = function isMultiSelect(element) {
    return element.options && element.multiple;
};

/**
  * Retrieves the selected options from a multi-select as an array.
  * @param  {HTMLOptionsCollection} options  the options for the select
  * @return {Array}                          an array of selected option values
*/
var getSelectValues = function getSelectValues(options) {
    return [].reduce.call(options, function (values, option) {
        return option.selected ? values.concat(option.value) : values;
    }, []);
};

// This is the function that is called on each element of the array.
var reducerFunction = function reducerFunction(data, element) {

    // Add the current field to the object.
    data[element.name] = element.value;

    // For the demo only: show each step in the reducer’s progress.
    console.log(JSON.stringify(data));

    return data;
};

/**
  * Retrieves input data from a form and returns it as a JSON object.
  * @param  {HTMLFormControlsCollection} elements  the form elements
  * @return {Object}                               form data as an object literal
  */
var formToJSON = function formToJSON(elements)
{
    return [].reduce.call(elements, function (data, element) {
        // Make sure the element has the required properties and
        // should be added.
        if (isValidElement(element) && isValidValue(element)) {
            /*
             * Some fields allow for more than one value, so we need to check if this
             * is one of those fields and, if so, store the values as an array.
             */
            if (isCheckbox(element)) {
                var values = (data[element.name] || []).concat(element.value);
                if (values.length == 1){
                values = values[0];
                }
                data[element.name] = values;
            } else if (isMultiSelect(element)) {
                data[element.name] = getSelectValues(element);
            } else {
                data[element.name] = element.value;
            }
        }

        return data;
    },
    {});
};

