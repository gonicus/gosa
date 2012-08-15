qx.Class.define("cute.Session",
{
    statics:
    {

        /*! \brief  The currently logged in user as JS object.
         *          If nobody is logged in, it is 'null'.
         */
        user: null,


        /*! \brief  Returns the currently logged in user object.
         */
        getUser: function(){
            return(cute.Session.user);
        }
    }
});
