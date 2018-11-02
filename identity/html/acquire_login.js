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
//var identity_public_pem = "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUFwY2VYaWVNS0xYL3Z4M1lwSUljRApDcGFkdTRnQUNsZWdaTDRIeS9DYXFTSC9pcDIwWFdjN24wUGp6eEkzbHdidXhOb1pkWHlud2QvYXV6LzFmMUpJCmNaS28yVzVSMFhISHMvWXpHdWhuODhjTm5kQkplaVkvZ2dWdEJ4WWhHVWJkWVl3ekRBeDBjVXd0RXJhYi9yNk0KVUFWaXBTRkJyZ2VIN2tJLzJ3MGt4ckNxQU9Cay95S1h6TXdLMnBWdklMR2VRZzdKSkZKQytxeHVqdVdOL20vaApuY0ZFUkRZVXl0NUNHUmdBTjNNQkNueVZmVzRXUzV0bFhvN0Z2YzhjYW9mUFBzSWpXWkkxdVEwRExpYk9RMkFuCnlhU2d2MytqK1RjQ1RrYnVJUTdiSmUwM09sb3dJWVRtTTEzcWZJK3V4Z0hvRzdCL3dJck4yRWJsd2Z3MjZNR3MKZ3dJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg==";

/*
function generateKey(alg, scope) {
return new Promise(function(resolve) {
    var genkey = crypto.subtle.generateKey(alg, true, scope)
    genkey.then(function (pair) {
    resolve(pair)
    })
})
}
function arrayBufferToBase64String(arrayBuffer) {
var byteArray = new Uint8Array(arrayBuffer)
var byteString = ''
for (var i=0; i<byteArray.byteLength; i++) {
    byteString += String.fromCharCode(byteArray[i])
}
return btoa(byteString)
}
function textToArrayBuffer(str) {
var buf = unescape(encodeURIComponent(str)) // 2 bytes for each char
var bufView = new Uint8Array(buf.length)
for (var i=0; i < buf.length; i++) {
    bufView[i] = buf.charCodeAt(i)
}
return bufView
}
function arrayBufferToText(arrayBuffer) {
var byteArray = new Uint8Array(arrayBuffer)
var str = ''
for (var i=0; i<byteArray.byteLength; i++) {
    str += String.fromCharCode(byteArray[i])
}
return str
}
function arrayBufferToBase64(arr) {
return btoa(String.fromCharCode.apply(null, new Uint8Array(arr)))
}
function convertBinaryToPem(binaryData, label) {
var base64Cert = arrayBufferToBase64String(binaryData)
var pemCert = "-----BEGIN " + label + "-----\r\n"
var nextIndex = 0
var lineLength
while (nextIndex < base64Cert.length) {
    if (nextIndex + 64 <= base64Cert.length) {
    pemCert += base64Cert.substr(nextIndex, 64) + "\r\n"
    } else {
    pemCert += base64Cert.substr(nextIndex) + "\r\n"
    }
    nextIndex += 64
}
pemCert += "-----END " + label + "-----\r\n"
return pemCert
}

function importPrivateKey(pemKey) {
return new Promise(function(resolve) {
    var importer = crypto.subtle.importKey("pkcs8", convertPemToBinary(pemKey), signAlgorithm, true, ["sign"])
    importer.then(function(key) {
    resolve(key)
    })
})
}
function exportPublicKey(keys) {
return new Promise(function(resolve) {
    window.crypto.subtle.exportKey('spki', keys.publicKey).
    then(function(spki) {
    resolve(convertBinaryToPem(spki, "RSA PUBLIC KEY"))
    })
})
}
function exportPrivateKey(keys) {
return new Promise(function(resolve) {
    var expK = window.crypto.subtle.exportKey('pkcs8', keys.privateKey)
    expK.then(function(pkcs8) {
    resolve(convertBinaryToPem(pkcs8, "RSA PRIVATE KEY"))
    })
})
}
function exportPemKeys(keys) {
return new Promise(function(resolve) {
    exportPublicKey(keys).then(function(pubKey) {
    exportPrivateKey(keys).then(function(privKey) {
        resolve({publicKey: pubKey, privateKey: privKey})
    })
    })
})
}
function signData(key, data) {
return window.crypto.subtle.sign(signAlgorithm, key, textToArrayBuffer(data))
}
function testVerifySig(pub, sig, data) {
return crypto.subtle.verify(signAlgorithm, pub, sig, data)
}
function encryptData(vector, key, data) {
return crypto.subtle.encrypt(
    {
    name: "RSA-OAEP",
    iv: vector
    },
    key,
    textToArrayBuffer(data)
)
}
function decryptData(vector, key, data) {
return crypto.subtle.decrypt(
    {
        name: "RSA-OAEP",
        iv: vector
    },
    key,
    data
)
}
// Test everything
var signAlgorithm = {
name: "RSASSA-PKCS1-v1_5",
hash: {
    name: "SHA-256"
},
modulusLength: 2048,
extractable: false,
publicExponent: new Uint8Array([1, 0, 1])
}
*/

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

/** Function to convert a base64 string to an array buffer */
function base64StringToArrayBuffer(b64str) {
    var byteStr = atob(b64str)
    var bytes = new Uint8Array(byteStr.length)
    for (var i = 0; i < byteStr.length; i++) {
        bytes[i] = byteStr.charCodeAt(i)
    }
    return bytes.buffer
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

/** Function to convert pemfile info binary data used for js crypto */
function convertPemToBinary(pem) {
    var lines = pem.split('\n')
    var encoded = ''
    for(var i = 0;i < lines.length;i++){
        if (lines[i].trim().length > 0 &&
            lines[i].indexOf('-BEGIN PRIVATE KEY-') < 0 &&
            lines[i].indexOf('-BEGIN PUBLIC KEY-') < 0 &&
            lines[i].indexOf('-END PRIVATE KEY-') < 0 &&
            lines[i].indexOf('-END PUBLIC KEY-') < 0) {
        encoded += lines[i].trim()
        }
    }
    console.log(encoded);
    return base64StringToArrayBuffer(encoded)
}

/** Function to import and return the public key from the passed pemfile */
 async function importPublicKey(pemKey) {
    //convert the pem key to binary
    var bin = convertPemToBinary(pemKey);

    var encryptAlgorithm = {
        name: "RSA-OAEP",
        modulusLength: 2048,
        publicExponent: 65537,
        extractable: false,
        hash: {
            name: "SHA-256"
        }
    };

    var public_key = await crypto.subtle.importKey(
                        "spki", bin, encryptAlgorithm,
                        true, ["encrypt"]
                        );

    console.log(public_key)

    return public_key;
}

/** Function to load the public key of the identity service */
async function getIdentityPublicKey(){
    var pem = getIdentityPublicPem();
    return await importPublicKey(pem);
}

/** Function that encrypts the passed data with the passed public key */
async function encryptData(key, data){
    if (typeof data === 'string' || data instanceof String){
        data = string_to_utf8_bytes(data);
    }

    console.log(`INPUT = ${data}`);
    console.log(data.buffer);

    key = await key;

    let result = await window.crypto.subtle.encrypt(
                    {
                        name: "RSA-OAEP"
                    },
                    key,
                    data.buffer
                );

    var output = new Uint8Array(result);

    console.log(`OUTPUT = ${output} | ${output.length}`)

    return output;
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

