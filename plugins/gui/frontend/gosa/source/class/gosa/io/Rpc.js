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
 * @lint ignoreReferenceField(converter,queue)
 * @ignore(qx.core.ServerSettings.serverPathSuffix)
 * */
qx.Class.define("gosa.io.Rpc", {

  type: "singleton",

  extend: qx.io.remote.Rpc,

  construct: function(){
    this.base(arguments);

    this.setUrl(gosa.Config.url);
    this.setServiceName(gosa.Config.service);
    this.setTimeout(gosa.Config.timeout);

    // Hook into parse and stringify to detect class hints
    this.setParseHook(this._putMeIntoContext(this._parseHook));

    this.converter.push(gosa.io.types.Timestamp);
    this.converter.push(gosa.io.types.Binary);

    this.__cacheHashRegex = new RegExp('^###([^#]+)###(.*)');

    // these RPCs are always allowed, even when all others are blocked
    this.cA("getNoLoginMethods").then(function(res) {
      this.__allowedRPCs = res;
    }, this);
  },

  properties: {

    /**
     * Reviver function to call when parsing JSON responses. Null if no
     * preprocessing is used.
     */
    parseHook :
    {
      check : "Function",
      nullable : true
    },

    /**
     * Block all RPC-Promised from beeing fullfilled, e.g to allow a login to succeed before
     * executing the RPC
     */
    blockRpcs: {
      check: "Boolean",
      init: false,
      event: "changeBlockRpcs"
    }
  },

  statics: {

    /**
     * Resolve an error code to an translated text.
     */
    resolveError: function(old_error){
      var rpc = gosa.io.Rpc.getInstance();
      return new qx.Promise(function(resolve, reject) {
        rpc.cA("getError", old_error.field, gosa.Tools.getLocale())
        .then(function(data) {
          // The default error message attribute is 'message'
          // so fill it with the incoming message
          data.message = data.text;
          if("details" in data){
            for(var item in data.details) {
              if (data.details.hasOwnProperty(item)) {
                data.message += " - " + data.details[item]['detail'];
              }
            }
          }
          reject(new gosa.core.RpcError(data));
        }, function() {
          if(!old_error.message){
            old_error.message = old_error.text;
          }
          reject(new gosa.core.RpcError(old_error));
        });
      }, this);
    }
  },

  members: {
    queue: [],
    converter: [],
    running: false,
    __xsrf : null,
    __cacheHashRegex: null,
    __allowedRPCs: null,


    /* Enables an anonymous method to use the this context.
     * This is used for parsing the incoming json.
     * */
    _putMeIntoContext: function(func)
    {
      var self = this;
      var f = function(){
        return func.apply(self, arguments);
      };
      return(f);
    },

    /* Parse the incoming json-data.
     * Transform transmitted objects (those with a __jsonclass__ tag)
     * into real objects.
     * */
    _parseHook: function(key, value){
      if(value && typeof(value) == "object" && "__jsonclass__" in value){
        for(var converted_id in this.converter){
          if(this.converter[converted_id].tag == value['__jsonclass__']){
            var converter = new this.converter[converted_id]();
            converter.fromJSON(value);
            return(converter);
          }
        }
      }
      return(value);
    },

    // overridden
    createRequest: function()
    {
      var req = this.base(arguments);
      req.setRequestHeader("X-XSRFToken", this.__xsrf);
      return req;
    },

    /**
     * Return the XSRF Token for the current session
     * @return {String}
     */
    getXsrfToken: function() {
      return this.__xsrf;
    },

    /**
     * Create a {qx.Promise} for the RPC call
     * @param argx {Array} arguments for the RPC call
     * @return {qx.Promise}
     * @private
     */
    __promiseCallAsync: function(argx) {
      this.debug("started next rpc job '" + argx[0] + "'");
      return new qx.Promise(function(resolve, reject) {
        if (this.isBlockRpcs() && this.__allowedRPCs.indexOf(argx[0]) === -1) {
          this.debug("RPCs are currently blocked: listening for unblock event");
          this.addListenerOnce("changeBlockRpcs", function() {
            this.__executeCallAsync(argx, resolve, reject);
          })
        } else {
          this.__executeCallAsync(argx, resolve, reject);
        }
      }, this);
    },

    /**
     * Execute the RPC call
     * @param argx {Array} arguments for the call
     * @param resolve {Function} qx.Promise resolve function
     * @param reject {Function} qx.Promise reject function
     * @private
     */
    __executeCallAsync : function(argx, resolve, reject) {
      var cachedCall = argx[0].startsWith("**");
      var cachedResult = null;
      if (cachedCall) {
        var cacheParams = argx.join(",");
        cachedResult = this.getCachedResponse(cacheParams);
        if (cachedResult) {
          // we do have the response in a cache -> add hash as second parameter after the method name
          qx.lang.Array.insertAt(argx, cachedResult.hash, 1);
        } else {
          qx.lang.Array.insertAt(argx, "0", 1);
        }
      }
      this.callAsync.apply(this, [
        function(result, error) {
          if (error) {
            this.debug("rpc job failed '" + argx[0] + "'");
            reject(error);
          }
          else {
            var cacheStatus = "not used";
            if (cachedCall) {
              // cached call
              if (result.hash) {
                if (cachedResult && result.hash === cachedResult.hash) {
                  // cache hit, use the cached response
                  cacheStatus = "HIT";
                  result = cachedResult.response;
                }
                else {
                  // file has changed, save the response in cache
                  cacheStatus = "MISS";
                  this.setCachedResponse(cacheParams, result);
                  result = result.response;
                }
              }
            }
            this.debug("rpc job finished '" + argx[0] + "', cache: "+cacheStatus);
            resolve(result);
          }
        }.bind(this)
      ].concat(argx));
    },

    /**
     * Handle rpc errors and re-trigger the RPC oif necessary
     * @param argx {Array} the arguments from the errored RPC
     * @param error {Error}
     * @return {var}
     * @private
     */
    __handleRpcError: function(argx, error) {
      if(error && error.code == 401) {
        this.setBlockRpcs(true);

        gosa.Session.getInstance().setUser(null);
        this.debug("RPC "+argx[0]+" failed: authorization error");

        var dialog = gosa.ui.dialogs.LoginDialog.openInstance();
        return new qx.Promise(function(resolve, reject) {
          dialog.addListener("login", function(e) {

            // Query for the users Real Name
            gosa.Session.getInstance().setUser(e.getData()['user']);

            // Re-connect SSE
            var messaging = gosa.io.Sse.getInstance();
            messaging.reconnect();

            // retry the call
            this.debug("retrying RPC "+argx[0]+" after successful authorization");
            this.__promiseCallAsync(argx).then(resolve, reject);
            this.setBlockRpcs(false);
          }, this);
        }, this);

        // Catch potential errors here.
      } else if(error && error.code != 500 && (error.code >= 400 || error.code == 0)){

        var msg = error.message;
        if(error.code == 0){
          msg = new qx.ui.core.Widget().tr("Communication with the backend failed!");
        }

        var d = new gosa.ui.dialogs.RpcError(msg);
        return new qx.Promise(function(resolve, reject) {
          d.addListener("retry", function(){
            this.__promiseCallAsync(argx).then(resolve, reject);
          }, this);
          d.open();
        }, this);
      } else if (error && argx[0] != "getError") {
        // Parse additional information out of the error.message string.
        error.field = null;

        // Check for "<field> error-message" formats
        var match = error.message.match(/<([a-zA-Z0-9\-_ ]*)>[ ]*(.*)$/);
        if (match) {
          error.field = match[1];
          error.message = match[2];
          return gosa.io.Rpc.resolveError(error, this);
        }
      }
    },

    /* This method pushes a new request into the rpc-queue and then
     * triggers queue-processing.
     */
    cA : function() {
      var argx = Array.prototype.slice.call(arguments, 0);
      if (!this.__xsrf) {
        // Do a simple GET
        return new qx.Promise(function(resolve, reject) {
          var req = new qx.io.request.Xhr(this.getUrl());
          req.addListener("success", function() {
            resolve(qx.bom.Cookie.get("_xsrf"));
          });
          req.addListener("fail", function(e) {
            reject(e.toString());
          });
          req.send();
        }, this)
        .catch(function(error) {
          var d = new gosa.ui.dialogs.RpcError(error.toString());
          d.show();
        })
        .then(function(xsrf) {
          this.__xsrf = xsrf;
          return this.__promiseCallAsync(argx).catch(function(error) {
            return this.__handleRpcError(argx, error);
          }, this);
        }, this)
      } else {
        return this.__promiseCallAsync(argx).catch(function(error) {
          return this.__handleRpcError(argx, error);
        }, this);
      }
    },

    /**
     * Internal RPC call method
     *
     * @lint ignoreDeprecated(eval)
     *
     * @param args {Array}
     *   array of arguments
     *
     * @param callType {Integer}
     *   0 = sync,
     *   1 = async with handler,
     *   2 = async event listeners
     *
     * @param refreshSession {Boolean}
     *   whether a new session should be requested
     *
     * @return {var} the method call reference.
     * @throws {Error} An error.
     */
    _callInternal : function(args, callType, refreshSession)
    {
      var self = this;
      var offset = (callType == 0 ? 0 : 1);
      var whichMethod = (refreshSession ? "refreshSession" : args[offset]);
      var handler = args[0];
      var argsArray = [];
      var eventTarget = this;
      var protocol = this.getProtocol();

      for (var i=offset+1; i<args.length; ++i)
      {
        argsArray.push(args[i]);
      }

      var req = this.createRequest();

      // Get any additional out-of-band data to be sent to the server
      var serverData = this.getServerData();

      // Create the request object
      var rpcData = this.createRpcData(req.getSequenceNumber(),
          whichMethod,
          argsArray,
          serverData);

      req.setCrossDomain(this.getCrossDomain());

      if (this.getUsername())
      {
        req.setUseBasicHttpAuth(this.getUseBasicHttpAuth());
        req.setUsername(this.getUsername());
        req.setPassword(this.getPassword());
      }

      req.setTimeout(this.getTimeout());
      var ex = null;
      var id = null;
      var result = null;
      var response = null;

      var handleRequestFinished = function(eventType, eventTarget)
      {
        switch(callType)
        {
          case 0: // sync
            break;

          case 1: // async with handler function
            handler(result, ex, id);
            break;

          case 2: // async with event listeners
            // Dispatch the event to our listeners.
            if (!ex)
            {
              eventTarget.fireDataEvent(eventType, response);
            }
            else
            {
              // Add the id to the exception
              ex.id = id;

              if (args[0])      // coalesce
              {
                // They requested that we coalesce all failure types to
                // "failed"
                eventTarget.fireDataEvent("failed", ex);
              }
              else
              {
                // No coalese so use original event type
                eventTarget.fireDataEvent(eventType, ex);
              }
            }
        }
      };

      var addToStringToObject = function(obj)
      {
        if (protocol == "qx1")
        {
          obj.toString = function()
          {
            switch(obj.origin)
            {
              case qx.io.remote.Rpc.origin.server:
                return "Server error " + obj.code + ": " + obj.message;

              case qx.io.remote.Rpc.origin.application:
                return "Application error " + obj.code + ": " + obj.message;

              case qx.io.remote.Rpc.origin.transport:
                return "Transport error " + obj.code + ": " + obj.message;

              case qx.io.remote.Rpc.origin.local:
                return "Local error " + obj.code + ": " + obj.message;

              default:
                return ("UNEXPECTED origin " + obj.origin +
                    " error " + obj.code + ": " + obj.message);
            }
          };
        }
        else // protocol == "2.0"
        {
          obj.toString = function()
          {
            var             ret;

            ret =  "Error " + obj.code + ": " + obj.message;
            if (obj.data)
            {
              ret += " (" + obj.data + ")";
            }

            return ret;
          };
        }
      };

      var makeException = function(origin, code, message)
      {
        var ex = new Error();

        if (protocol == "qx1")
        {
          ex.origin = origin;
        }
        ex.code = code;
        ex.message = message;
        addToStringToObject(ex);

        return ex;
      };

      req.addListener("failed", function(evt)
          {
            var code = evt.getStatusCode();
            var message = qx.io.remote.Exchange.statusCodeToString(code);
            try {
              var content = qx.lang.Json.parse(evt.getContent());
              if (content.error) {
                message = content.error.message;
              }
            } catch(e) {}
            ex = makeException(qx.io.remote.Rpc.origin.transport,
              code,
              message);
            id = this.getSequenceNumber();
            handleRequestFinished("failed", eventTarget);
          });

      req.addListener("timeout", function()
          {
            this.debug("TIMEOUT OCCURRED");
            ex = makeException(qx.io.remote.Rpc.origin.local,
              qx.io.remote.Rpc.localError.timeout,
              "Local time-out expired for "+ whichMethod);
            id = this.getSequenceNumber();
            handleRequestFinished("timeout", eventTarget);
          });

      req.addListener("aborted", function()
          {
            ex = makeException(qx.io.remote.Rpc.origin.local,
              qx.io.remote.Rpc.localError.abort,
              "Aborted " + whichMethod);
            id = this.getSequenceNumber();
            handleRequestFinished("aborted", eventTarget);
          });

      req.addListener("completed", function(evt)
          {
            response = evt.getContent();

            // Parse. Skip when response is already an object
            // because the script transport was used.
            if (!qx.lang.Type.isObject(response)) {

              // Handle converted dates
              if (self._isConvertDates()) {

                // Parse as JSON and revive date literals
                if (self._isResponseJson()) {
                  response = qx.lang.Json.parse(response, function(key, value) {
                    if (value && typeof value === "string") {
                      if (value.indexOf("new Date(Date.UTC(") >= 0) {
                        var m = value.match(/new Date\(Date.UTC\((\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\)\)/);
                        return new Date(Date.UTC(m[1],m[2],m[3],m[4],m[5],m[6],m[7]));
                      }
                    }
                    return value;
                  });

                  // Eval
                } else {
                  response = response && response.length > 0 ? eval('(' + response + ')') : null;
                }

                // No special date handling required, JSON assumed
              } else {
                response = qx.lang.Json.parse(response, self.getParseHook());
              }
            }

            id = response["id"];

            if (id != this.getSequenceNumber())
            {
              this.warn("Received id (" + id + ") does not match requested id " +
                  "(" + this.getSequenceNumber() + ")!");
            }

            // Determine if an error was returned. Assume no error, initially.
            var eventType = "completed";
            var exTest = response["error"];

            if (exTest != null)
            {
              // There was an error
              result = null;
              addToStringToObject(exTest);
              ex = exTest;

              // Change the event type
              eventType = "failed";
            }
            else
            {
              result = response["result"];

              if (refreshSession)
              {
                result = eval("(" + result + ")");
                var newSuffix = qx.core.ServerSettings.serverPathSuffix;
                if (self.__currentServerSuffix != newSuffix)
                {
                  self.__previousServerSuffix = self.__currentServerSuffix;
                  self.__currentServerSuffix = newSuffix;
                }

                self.setUrl(self.fixUrl(self.getUrl()));
              }
            }

            handleRequestFinished(eventType, eventTarget);
          });

      // Provide a replacer when convert dates is enabled
      var replacer = null;
      if (this._isConvertDates()) {
        replacer = function(key, value) {
          // The value passed in is of type string, because the Date's
          // toJson gets applied before. Get value from containing object.
          value = this[key];

          if (qx.lang.Type.isDate(value)) {
            var dateParams =
              value.getUTCFullYear() + "," +
              value.getUTCMonth() + "," +
              value.getUTCDate() + "," +
              value.getUTCHours() + "," +
              value.getUTCMinutes() + "," +
              value.getUTCSeconds() + "," +
              value.getUTCMilliseconds();
            return "new Date(Date.UTC(" + dateParams + "))";
          }
          return value;
        };
      }

      req.setData(qx.lang.Json.stringify(rpcData, replacer));
      req.setAsynchronous(callType > 0);

      if (req.getCrossDomain())
      {
        // Our choice here has no effect anyway.  This is purely informational.
        req.setRequestHeader("Content-Type",
            "application/x-www-form-urlencoded");
      }
      else
      {
        // When not cross-domain, set type to text/json
        req.setRequestHeader("Content-Type", "application/json");
      }

      // Do not parse as JSON. Later done conditionally.
      req.setParseJson(false);
      req.send();

      if (callType == 0)
      {
        if (ex != null)
        {
          var error = new Error(ex.toString());
          error.rpcdetails = ex;
          throw error;
        }
        return result;
      }
      else
      {
        return req;
      }
    },

    /**
     * Retrieves the cached repsonse from an old RPC call
     *
     * @param paramString {String} concatenated parameters of the RPC call
     * @return {String} RPC call result
     */
    getCachedResponse: function(paramString) {
      return qx.bom.Storage.getLocal().getItem(paramString);
    },

    /**
     * Saves an RPC-Call result in the {qx.bom.Storage}
     *
     * @param paramString {String} concatenated parameters of the RPC call
     * @param result {String} RPC call result
     */
    setCachedResponse: function(paramString, result) {
      qx.bom.Storage.getLocal().setItem(paramString, result);
    }
  }
});
