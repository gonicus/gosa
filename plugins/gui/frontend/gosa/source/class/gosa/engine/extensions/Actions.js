/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

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
        if (this._isActionAllowed(action, context)) {  // actions without permission are not shown
          this._processAction(action, target, context);
        }
      }, this);
    },

    /**
     * Checks if the user has the permission to execute the action.
     *
     * @param action {Map} The action node
     * @param context {gosa.engine.Context}
     * @return {Boolean}
     */
    _isActionAllowed : function(action, context) {
      qx.core.Assert.assertMap(action);
      qx.core.Assert.assertTrue(action.hasOwnProperty("dialog") || action.hasOwnProperty("target"));

      // check target
      if (action.hasOwnProperty("target")) {
        qx.core.Assert.assertString(action.target);
        var methodName = /^([^(]+)\((.*)\)$/.exec(action.target)[1];
        qx.core.Assert.assertString(methodName);
        qx.core.Assert.assertFalse(methodName === "");

        if (!context.getActionController().hasMethod(methodName)) {
          return false;
        }
      }

      // check dialog
      if (action.hasOwnProperty("dialog")) {
        qx.core.Assert.assertString(action.dialog);
        gosa.util.Template.getDialogRpc(action.dialog);
        var clazz = gosa.ui.dialogs.actions[action.dialog];
        var rpcList = clazz.RPC_CALLS;
        var session = gosa.Session.getInstance();

        // user must be allowed to enhance each rpc
        return rpcList.every(session.isCommandAllowed, session);
      }

      return true;
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
      var type = data.hasOwnProperty("type") ? data.type : "menu";

      switch(type) {

        case "afterDialog":
          // this action should ba called on the beforeClose event of an dialog
          context.addAfterDialogAction(data.name, function(ev) {
            // 1. collect data from dialog form
            var values = {};
            var dialogContext = ev.getTarget().getContext();
            var widgetMap = dialogContext.getFreeWidgetRegistry().getMap();
            Object.getOwnPropertyNames(widgetMap).forEach(function(key) {
              var val = widgetMap[key].getValue();
              values[key] = gosa.ui.widgets.Widget.getSingleValue(val);
            });

            var args = this.__createArgumentsList(data.target, context);
            args.push(qx.lang.Json.stringify(values));

            // 2. send data to command
            context.getActionController().callMethod.apply(context.getActionController(), args)
            .then(function(result) {
              this.info(this, "Call of method '" + args[0] + "' was successful and returned '" + result + "'");
              // apply returned values to object
              var obj = context.getObject();
              Object.getOwnPropertyNames(result).forEach(function(attr) {
                obj.set(attr, new qx.data.Array(result[attr]));
              }, this);
              return null;
            }, this)
            .catch(function(error) {
              new gosa.ui.dialogs.Error(error).open();
            });
          }, this);
          break;

        default:
          var button = new qx.ui.menu.Button(data.text, context.getResourceManager().getResource(data.icon), command);
          button.setAppearance("icon-menu-button");

          // condition
          if (data.hasOwnProperty("condition")) {
            button.addListener("appear", function() {
              this._checkCondition(data.condition, context).then(function(result) {
                button.setEnabled(result);
              });
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
              dialog.open();

              context.addDialog(dialog);
            });
          }

          // listener to invoke target
          if (data.hasOwnProperty("target")) {
            this._addExecuteTargetListener(data.target, button, context);
          }

          context.addActionMenuEntry(data.name, button);
          break;
      }
    },

    /**
     * Check if the given condition is satisfied.
     *
     * @param condition {String} Complete condition string as saved in the template
     * @param context {gosa.engine.Context}
     */
    _checkCondition : function(condition, context) {
      qx.core.Assert.assertString(condition);
      var res;
      var promises = [];

      if (condition.indexOf("&&") >= 0) {
        return new qx.Promise(function(resolve, reject) {
          res = true;

          condition.split("&&").forEach(function(part) {
            promises.push(this._checkConditionPart(part.trim(), context));
          }, this);

          qx.Promise.all(promises).then(function(results) {
            results.some(function(val) {
              if (val === false) {
                res = false;
                resolve(false);
              }
            });
            resolve(true);
          }).catch(reject);
        }, this);
      } else if (condition.indexOf("||") >= 0) {
        return new qx.Promise(function(resolve, reject) {
          res = false;

          condition.split("||").forEach(function(part) {
            promises.push(this._checkConditionPart(part.trim(), context));
          }, this);

          qx.Promise.all(promises).then(function(results) {
            results.some(function(val) {
              if (val === true) {
                res = true;
                resolve(true);
              }
            });
            resolve(false);
          }).catch(reject);
        }, this);
      } else {
        return this._checkConditionPart(condition, context);
      }
    },

    _checkConditionPart: function(condition, context) {
      // get configuration for condition rpc
      var parser = /^(!)?([^(!=]*)(\((.*)\))?([!=]*)(.*)$/;
      var parsed = parser.exec(condition);
      var name = parsed[2];
      var negated = parsed[1] === "!";

      var comparisonOperator = parsed[5];
      var compareTo = parsed[6];
      if (compareTo) {
        if (compareTo[0] === "'" || compareTo[0] === "\"") {
          compareTo = compareTo.replace(/^["']/, "").replace(/["']$/, "");
        } else {
          compareTo = gosa.ui.widgets.Widget.getSingleValue(context.getActionController().getAttributeValue(compareTo));
        }
      }

      function doCompare(value) {
        var res = false;
        if (compareTo && comparisonOperator) {
          switch (comparisonOperator) {
            case "!=":
              return compareTo != value;
            case "!==":
              return compareTo !== value;
            case "==":
              return compareTo == value;
            case "===":
              return compareTo === value;
            case "<=":
              return compareTo <= value;
            case ">=":
              return compareTo >= value;
          }
        } else {
          res = !!gosa.ui.widgets.Widget.getSingleValue(value);

          // negation
          if (negated) {
            res = !res;
          }
          return res;
        }
      }

      // conditions with (.*) are rpc; all others are attributes of the object
      if (parsed[4] || parsed[3] === "()") {
        // method call

        // build arguments for rpc call
        var args = [];
        if (parsed[4]) {  // has arguments
          parsed[4].split(",").forEach(function(arg) {
            arg = arg.trim();
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
              var value = context.getActionController().getAttributeValue(arg);
              args.push(gosa.ui.widgets.Widget.getSingleValue(value));
            }
          });
        }

        // invoke rpc
        var rpc = gosa.io.Rpc.getInstance();
        return rpc.cA.apply(rpc, [name].concat(args))
        .then(function(result) {
          return doCompare(result);
        }, this)
        .catch(function(error) {
          new gosa.ui.dialogs.Error(error).open();
        });
      }
      else {
        // object attribute
        var value = context.getActionController().getAttributeValue(name);
        return qx.Promise.resolve(doCompare(value));
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

      var args = this.__createArgumentsList(target, context);
      // listener for invoking the target
      button.addListener("execute", function() {

        context.getActionController().callMethod.apply(context.getActionController(), args)
        .then(function(result) {
          qx.log.Logger.info("Call of method '" + args[0] + "' was successful and returned '" + result + "'");
        })
        .catch(function(error) {
          new gosa.ui.dialogs.Error(error).open();
        });
      }, this);
    },

    __createArgumentsList: function(target, context) {
      var parser = /^([^(]+)\((.*)\)$/;
      var parsed = parser.exec(target);
      var methodName = parsed[1];
      var params = parsed[2];
      var args = [];

      // create argument list
      if (qx.lang.Type.isString(params) && params !== "") {
        params = params.split(",");
        var paramParser = /%\(([^)]+)\)s/;
        var paramType = /\s*['"]([^'"]+)['"]\s*/;

        params.forEach(function(param) {
          var match = paramParser.exec(param);
          if (match) {
            var data = gosa.ui.widgets.Widget.getSingleValue(context.getActionController().getProperty(match[1]));
            args.push(param.replace(match[0], data));
          } else {
            var typeMatch = paramType.exec(param);
            if (typeMatch) {
              args.push(typeMatch[1]);
            }
          }
        });
      }
      args.unshift(methodName);
      return args;
    }
  },

  defer : function() {
    gosa.engine.ExtensionManager.getInstance().registerExtension("actions", gosa.engine.extensions.Actions);
  }
});
