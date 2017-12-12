from logging import getLogger


class Validator:
    def __init__(self, context):
        self.log = getLogger(__name__)
        self._context = context

    def process_validator(self, fltr, key, value, props_copy, **kwargs):
        """
        This method processes a given process-list (fltr) for a given property (prop).
        And return TRUE if the value matches the validator set and FALSE if
        not.
        """

        # This is our process-line pointer it points to the process-list line
        #  we're executing at the moment
        lptr = 0

        # Our filter result stack
        stack = list()
        self.log.debug(" validator started (%s)" % key)
        self.log.debug("  value: %s" % (value,))

        # Process the list till we reach the end..
        lasterrmsg = ""
        errormsgs = []
        while (lptr + 1) in fltr:

            # Get the current line and increase the process list pointer.
            lptr += 1
            curline = fltr[lptr]

            # A condition matches for something and returns a boolean value.
            # We'll put this value on the stack for later use.
            if 'condition' in curline:

                # Build up argument list
                args = [props_copy, key, value] + [self._context if x == "__self__" else x for x in curline['params']]

                # Process condition and keep results
                fname = type(curline['condition']).__name__
                v, errors = (curline['condition']).process(*args, **kwargs)

                # Log what happend!
                self.log.debug("  %s: [Filter]  %s(%s) called and returned: %s" % (
                    lptr, fname, ", ".join(["\"" + x + "\"" for x in curline['params']]), v))

                # Append the result to the stack.
                stack.append(v)
                if not v:
                    if len(errors):
                        lasterrmsg = errors.pop()

            # A comparator compares two values from the stack and then returns a single
            #  boolean value.
            elif 'operator' in curline:
                v1 = stack.pop()
                v2 = stack.pop()
                fname = type(curline['operator']).__name__
                res = (curline['operator']).process(v1, v2)
                stack.append(res)

                # Add last error message
                if not res:
                    errormsgs.append(lasterrmsg)
                    lasterrmsg = ""

                # Log what happend!
                self.log.debug("  %s: [OPERATOR]  %s(%s, %s) called and returned: %s" % (
                    lptr, fname, v1, v2, res))

        # Attach last error message
        res = stack.pop()
        if not res and lasterrmsg != "":
            errormsgs.append(lasterrmsg)

        self.log.debug(" <- VALIDATOR ENDED (%s)" % key)
        return res, errormsgs
