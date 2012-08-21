/* ************************************************************************
#ignore(qx.core.ServerSettings)
#ignore(qx.core.ServerSettings.serverPathSuffix)
#ignore(qx.core.ServerSettings.serverPathPrefix)
#ignore(qx.core.ServerSettings.lastSessionRefresh)
#ignore(qx.core.ServerSettings.sessionTimeoutInSeconds)
*********************************************************************** */

qx.Class.define("cute.io.Rpc", {

  type: "singleton",

  extend: qx.io.remote.Rpc,

  construct: function(){
    this.base(arguments);

    this.setUrl(cute.Config.url);
    this.setServiceName(cute.Config.service);
    this.setTimeout(cute.Config.timeout);

    // Hook into parse and stringify to detect class hints
    this.setParseHook(this._putMeIntoContext(this._parseHook));

    this.converter.push(cute.io.types.Timestamp);
    this.converter.push(cute.io.types.Binary);
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
    }
  },

  members: {
    queue: [],
    converter: [],
    running: false,


    /* Enables an anonymous method to use the this context.
     * This is used for parsing the incoming json.
     * */
    _putMeIntoContext: function(func)
    {
      var self = this;
      var f = function(){
        return func.apply(self, arguments); 
      }
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

    /* We use a queue to process incoming RPC requests to ensure that we can
     * act on errors accordingly. E.g for error 401 we send a login request
     * first and then re-queue the current remote-procedure-call again.
     * */
    process_queue: function(){
      if(!this.running){
        if(this.queue.length){
          this.running = true;
          var item = this.queue.pop();
          this.debug("started next rpc job '" + item['arguments'][0] + "' (queued: " + this.queue.length + ")");
          this.callAsync.apply(this, [item['callback']].concat(item['arguments']));
        }
      }
    },

    /* This method pushes a new request into the rpc-queue and then
     * triggers queue-processing.
     * */
    cA : function(func, context) {

      // Create argument list
      var argx = Array.prototype.slice.call(arguments, 2);

      // Create queue object
      var call = {};
      call['arguments'] = argx;
      call['context'] = context;

      // This is the method that gets called when the rpc reqeust has finished
      var cl = this;
      call['callback'] = function(result, error){

        // Permission denied - show login screen to allow to log in.
        if(error && error.code == 401){

          var dialog = new cute.ui.dialogs.LoginDialog();
          dialog.open();
          dialog.addListener("login", function(e){
            cl.queue.push(call);
            cl.running = false;
            cl.process_queue();

            // Re-connect websockets
            var messaging = cute.io.WebSocket.getInstance();
            messaging.reconnect();
          }, cl);

          // Catch potential errors here. 
        }else if(error &&  error.code >= 400){

          var d = new cute.ui.dialogs.RpcError(error.message);
          d.addListener("retry", function(){
            cl.queue.push(call);
            cl.running = false;
            cl.process_queue();
          }, this);
          d.open();

        }else{

          // Parse additional information out of the error.message string.
          if(error){
            error.field = null;

            // Check for "<field> error-message" formats 
            if(error.message.match(/<[a-zA-Z0-9\-_ ]*>/)){
              error.field = error.message.replace(/<([a-zA-Z0-9\-_ ]*)>[ ]*(.*)$/, function(){ 
                  return(arguments[1])
                });
              error.message = error.message.replace(/<([a-zA-Z0-9\-_ ]*)>[ ]*(.*)$/, function(){ 
                  return(arguments[2])
                });
            }
          }

          // Everthing went fine, now call the callback method with the result.
          cl.running = false;
          cl.debug("rpc job finished '" + call['arguments'] + "' (queue: " + cl.queue.length + ")");
          func.apply(call['context'], [result, error]);

          // Start next rpc-job
          cl.process_queue();
        }
      };    

      // Insert the job into the job-queue and trigger processing.
      this.queue.unshift(call);
      this.process_queue();
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
        var ex = new Object();

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
            ex = makeException(qx.io.remote.Rpc.origin.transport,
              code,
              qx.io.remote.Exchange.statusCodeToString(code));
            id = this.getSequenceNumber();
            handleRequestFinished("failed", eventTarget);
          });

      req.addListener("timeout", function(evt)
          {
            this.debug("TIMEOUT OCCURRED");
            ex = makeException(qx.io.remote.Rpc.origin.local,
              qx.io.remote.Rpc.localError.timeout,
              "Local time-out expired for "+ whichMethod);
            id = this.getSequenceNumber();
            handleRequestFinished("timeout", eventTarget);
          });

      req.addListener("aborted", function(evt)
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
    }
  }
});
