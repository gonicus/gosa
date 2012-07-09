qx.Class.define("cute.io.Rpc", {

  type: "singleton",

  extend: qx.io.remote.Rpc,

  construct: function(){
    this.base(arguments);
    this.setUrl(cute.Config.url);
    this.setServiceName(cute.Config.service);
    this.setTimeout(cute.Config.timeout);
  },

  members: {
  
    queue: [],
    running: false,

    /* We use a queue to process incoming RPC requests to ensure that we can
     * act on errors accordingly. E.g for error 401 we send a login request
     * first and then re-queue the current remote-procedure-call again.
     * */
    process_queue: function(){
      if(!this.running){
        if(this.queue.length){
          this.debug("started next rpc job (queued: " + this.queue.length + ")");
          this.running = true;
          var item = this.queue.pop();
          this.callAsync.apply(this, [item['callback']].concat(item['arguments']));
        }
      }else{
        this.debug("triggered queue, but a job still running: " + this.queue.length + " jobs left");
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

              var dialog = new cute.ui.LoginDialog();
              dialog.open();
              dialog.addListener("login", function(e){
                  cl.queue.push(call);
                  cl.running = false;
                  cl.process_queue();
                }, cl);

            // Catch potential errors here. 
          }else if(error &&  error.code >= 400){
              cl.running = false;
              cl.error("unhandled error-code: " + error.code);
          }else{

            // Everthing went fine, now call the callback method with the result.
            cl.running = false;
            cl.debug("rpc job finished (queue: " + cl.queue.length + ")");
            func.apply(call['context'], [result, error]);

            // Start next rpc-job
            cl.process_queue();
          }
        };    

      // Insert the job into the job-queue and trigger processing.
      this.queue.unshift(call);
      this.debug("added new job to the queue (queue: " + this.queue.length + ")");
      this.process_queue();
    }
  }
});
