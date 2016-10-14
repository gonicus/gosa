/**
 * Reads and evaluates actions (e.g. "change password").
 */
qx.Class.define("gosa.engine.extensions.Actions", {
  extend : qx.core.Object,

  implement : [gosa.engine.extensions.IExtension],

  members : {

    process : function(data, target, context) {
      qx.core.Assert.assertArray(data, "Actions configuration must be an array");
      data.forEach(function(action) {
        this._processAction(action, target, context);
      }, this);
    },

    _processAction : function(data, target, context) {
      qx.core.Assert.assertMap(data, "Action configuration must be a hash map");
      qx.core.Assert.assertKeyInMap("name", data, "Action configuration must have the key 'name'");
      qx.core.Assert.assertKeyInMap("text", data, "Action configuration must have the key 'text'");

      // shortcut
      var command = null;
      if (data.hasOwnProperty("shortcut")) {
        command = new qx.ui.command.Command(data.shortcut);
      }

      // button creation
      var button = new qx.ui.menu.Button(data.text, context.getResourceManager().getResource(data.icon), command);
      button.setAppearance("icon-menu-button");

      // TODO: shortcuts, conditions, target, acl

      // condition
      if (data.hasOwnProperty("condition")) {
        button.addListenerOnce("appear", function() {
          this._checkCondition(data.condition, context, button.setEnabled, button);
        }, this);
      }

      // listener to open dialog
      if (data.hasOwnProperty("dialog")) {
        button.addListener("execute", function() {
          var clazz = qx.Class.getByName("gosa.ui.dialogs.actions." + data.dialog);
          if (!clazz) {
            qx.core.Assert.fail("Cannot find class for dialog '" + data.dialog + "'");
          }
          var dialog = new clazz(context.getActionController());
          dialog.setAutoDispose(true);

          if (data.hasOwnProperty("icon")) {
            dialog.setIcon(context.getResourceManager().getResource(data.icon));
          }
          dialog.open();
        });
      }

      // listener to invoke target
      if (data.hasOwnProperty("target")) {
        this._addExecuteTargetListener(data.target, button, context);
      }

      context.addActionMenuEntry(data.name, button);
    },

    /**
     * Check if the given condition is satisfied.
     *
     * @param condition {String} Complete condition string as saved in the template
     * @param context {gosa.engine.Context}
     * @param callback {Function} Called when the condition is checked, only parameter is a Boolean showing whether the
     *   condition is satisfied or not
     * @param callbackContext {Object ? null} Optional context for the callback function
     */
    _checkCondition : function(condition, context, callback, callbackContext) {
      qx.core.Assert.assertString(condition);
      qx.core.Assert.assertFunction(callback);

      // get configuration for condition rpc
      var parser = /^(!)?([^(]*)(\((.*)\))?$/;
      var parsed = parser.exec(condition);
      var name = parsed[2];
      var negated = parsed[1] === "!";
      var result = false;

      // conditions with arguments are rpc; all others are attributes of the object
      if (parsed[4]) {  // has arguments
        // method call

        // build arguments for rpc call
        var args = [];
        parsed[4].split(",").forEach(function(arg) {
          if (arg === "dn") {
            args.push(context.getActionController().getDn());
          }
          else if (arg === "uuid") {
            args.push(context.getActionController().getUuid());
          }
          else if (arg[0] === '"' || arg[0] === "'") {  // argument is a static string
            args.push(arg.replace(/^["']/, "").replace(/["']$/, ""));
          }
          else {  // attributes of object
            var value = context.getAttributeValue(arg);
            args.push(value && value.getLenth() > 0 ? value.getItem(0) : null);
          }
        });

        // invoke rpc
        var rpc = gosa.io.Rpc.getInstance();
        rpc.cA.apply(rpc, [function(result, error) {
          if (error) {
            new gosa.ui.dialogs.Error(error.message).open();
          }
          else {
            // negation
            if (negated) {
              result = !result;
            }

            callback.call(callbackContext, result);
          }
        }, this, name].concat(args));
      }
      else {
        // object attribute
        var value = context.getActionController().getAttributeValue(name);
        if (value.getLength() > 0) {
          result = !!value.getItem(0);
        }

        // negation
        if (negated) {
          result = !result;
        }

        callback.call(callbackContext, result);
      }
    },

    /**
     * Executes a given method (aka target) on the object.
     *
     * @param target {String} The unparsed target string as it apperas in the template
     * @param button {qx.ui.menu.Button} Button on which the listener shall be added
     * @param context {gosa.engine.Context}
     */
    _addExecuteTargetListener : function(target, button, context) {
      qx.core.Assert.assertString(target);
      qx.core.Assert.assertInstance(button, qx.ui.menu.Button);

      var parser = /^([^(]+)\((.*)\)$/;
      var parsed = parser.exec(target);
      var methodName = parsed[1];
      var params = parsed[2];
      var args = [];

      // create argument list
      if (qx.lang.Type.isString(params) && params !== "") {
        params = params.split(",");
        var paramParser = /%\(([^)]+)\)s/;

        params.forEach(function(param) {
          var match = paramParser.exec(param);
          if (match) {
            var data = context.getActionController().getProperty(match[1]);
            if (qx.lang.Type.isArray(data)) {
              args.push(param.replace(match[0], data[0]));
            }
            else {
              args.push(param.replace(match[0], data));
            }
          }
        });
      }

      // listener for invoking the target
      button.addListener("execute", function() {
        args.unshift(methodName, function(result, error) {
          if (error) {
            new gosa.ui.dialogs.Error(error.message).open();
          }
          else {
            qx.log.Logger.info("Call of method '" + methodName + "' was successful and returned '" + result + "'");
          }
        });
        context.getActionController().callMethod.apply(context.getActionController(), args);
      }, this);
    }
  },

  defer : function() {
    gosa.engine.ExtensionManager.getInstance().registerExtension("actions", gosa.engine.extensions.Actions);
  }
});
