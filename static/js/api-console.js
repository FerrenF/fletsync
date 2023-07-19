

function consoleAddLine(s){
  let output = $('#console-output')
  output.append('<p>'+s+'</p>');
}
function clearConsoleInput(){
  let console = $('#console-input-field');
  console.val("");
}
function runCommandInput(){
    let userId = $('#console-user-id').val(); // Get the selected API interface
    let selectedInterface = $('#interface-select').val(); // Get the selected API interface
    let apiUrl = '/tests/command';

    var inputString = $('#console-input-field').val();
    var commandRegex = /(\w+)\((?:(.*?)\))?/;

    var matches = inputString.match(commandRegex);
    if (matches) {
      var command = matches[1];
      var componentsString = matches[2];
      var parsedComponents = {'interface':selectedInterface, 'user_id':userId, 'operationName': command};
      if(componentsString) {
        var components = componentsString.split(',');


        components.forEach(function (component) {
          var [key, value] = component.split('=');
          parsedComponents[key.trim()] = value.trim();
        });
      }
      // Now you have the command and parsed components ready to use
      console.log('Command:', command);
      console.log('Components:', parsedComponents);
      console.log('Interface:', selectedInterface);

      let resp = $.post(apiUrl, parsedComponents).done(function(response){
       let input = $('#console-input-field').val()
       consoleAddLine('Command:' + input);
       consoleAddLine('Response:' + response);
       clearConsoleInput()
    })


    } else {
      consoleAddLine("Invalid command.");
    }

}

$(document).ready(function() {
  $('#api-interface-form').on('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

    runCommandInput();
  });
});