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

/** Also hard code the PEM data for the service's public key */
var identity_public_pem = "DATA";

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

  session_uid = vars["id"];

  if (session_uid){
      return session_uid;
  }

  document.clear();
  document.write("<p>INVALID SESSION UID</p>");
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

