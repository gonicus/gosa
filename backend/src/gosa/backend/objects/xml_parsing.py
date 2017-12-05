from gosa.backend.objects.comparator import get_comparator
from gosa.backend.objects.filter import get_filter
from gosa.backend.objects.operator import get_operator


class XmlParsing:
    def __init__(self, namespace='Objects'):
        self.__namespace = '{http://www.gonicus.de/%s}' % namespace

    def build_filter(self, element, out=None):
        """
        Attributes of objects can be filtered using in- and out-filters.
        These filters can manipulate the raw-values while they are read form
        the backend or they can manipulate values that have to be written to
        the backend.

        This method converts the read XML filter-elements of the defintion into
        a process lists. This list can then be easily executed line by line for
        each property, using the method:

        :meth:`gosa.backend.objects.object.Object.__processFilter`

        """

        # Parse each <FilterChain>, <Condition>, <ConditionChain>
        out = {}
        for el in element.iterchildren():
            if el.tag == "%sFilterChain" % self.__namespace:
                out = self.handleFilterChain(el, out)
            elif el.tag == "%sCondition" % self.__namespace:
                out = self.__handleCondition(el, out)
            elif el.tag == "%sConditionOperator" % self.__namespace:
                out = self.__handleConditionOperator(el, out)

        return out

    def handleFilterChain(self, element, out=None):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'FilterChain' element is handled here.

        Occurrence: OutFilter->FilterChain
        """
        if not out:
            out = {}

        # FilterChains can contain muliple "FilterEntry" tags.
        # But at least one.
        # Here we forward these elements to their handler.
        for el in element.iterchildren():
            if el.tag == "%sFilterEntry" % self.__namespace:
                out = self.__handleFilterEntry(el, out)
        return out

    def __handleFilterEntry(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'FilterEntry' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry
        """

        # FilterEntries contain a "Filter" OR a "Choice" tag.
        # Here we forward the elements to their handler.
        for el in element.iterchildren():
            if el.tag == "%sFilter" % self.__namespace:
                out = self.__handleFilter(el, out)
            elif el.tag == "%sChoice" % self.__namespace:
                out = self.__handleChoice(el, out)
        return out

    def __handleFilter(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'Filter' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Filter
        """

        # Get the <Name> and the <Param> element values to be able
        # to create a process list entry.
        name = element.__dict__['Name'].text
        params = []
        for entry in element.iterchildren():
            if entry.tag == "%sParam" % self.__namespace:
                params.append(entry.text)

        # Attach the collected filter and parameter value to the process list.
        cnt = len(out) + 1
        out[cnt] = {'filter': get_filter(name)(self), 'params': params}
        return out

    def __handleChoice(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'Choice' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice
        """

        # We just forward <When> tags to their handler.
        for el in element.iterchildren():
            if el.tag == "%sWhen" % self.__namespace:
                out = self.__handleWhen(el, out)
        return out

    def __handleWhen(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'When' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice->When
        """

        # (<When> tags contain a <ConditionChain>, a <FilterChain> tag and
        # an optional <Else> tag.
        #  The <FilterChain> is only executed when the <ConditionChain> matches
        #  the given values.)

        # Forward the tags to their correct handler.
        filterChain = {}
        elseChain = {}
        for el in element.iterchildren():
            if el.tag == "%sConditionChain" % self.__namespace:
                out = self.__handleConditionChain(el, out)
            if el.tag == "%sFilterChain" % self.__namespace:
                filterChain = self.handleFilterChain(el, filterChain)
            elif el.tag == "%sElse" % self.__namespace:
                elseChain = self.__handleElse(el, elseChain)

        # Collect jump points
        cnt = len(out)
        match = cnt + 2
        endMatch = match + len(filterChain)
        noMatch = endMatch + 1
        endNoMatch = noMatch + len(elseChain)

        # Add jump point for this condition
        cnt = len(out)
        out[cnt + 1] = {'jump': 'conditional', 'onTrue': match, 'onFalse': noMatch}

        # Add the <FilterChain> process.
        cnt = len(out)
        for entry in filterChain:
            cnt += 1
            out[cnt] = filterChain[entry]

        # Add jump point to jump over the else chain
        cnt = len(out)
        out[cnt + 1] = {'jump': 'non-conditional', 'to': endNoMatch}

        # Add the <Else> process.
        cnt = len(out)
        for entry in elseChain:
            cnt += 1
            out[cnt] = elseChain[entry]

        return out

    def __handleElse(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'Else' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice->Else
        """

        # Handle <FilterChain> elements of this else tree.
        for el in element.iterchildren():
            if el.tag == "%sFilterChain" % self.__namespace:
                out = self.handleFilterChain(el, out)

        return out

    def __handleConditionChain(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'ConditionChain' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice->When->ConditionChain
        """

        # Forward <Condition> tags to their handler.
        for el in element.iterchildren():
            if el.tag == "%sCondition" % self.__namespace:
                out = self.__handleCondition(el, out)
            elif el.tag == "%sConditionOperator" % self.__namespace:
                out = self.__handleConditionOperator(el, out)

        return out

    def __handleConditionOperator(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'ConditionOperator' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice->When->ConditionChain->ConditionOperator
        """

        # Forward <Left and <RightConditionChains> to the ConditionChain handler.
        out = self.__handleConditionChain(element.__dict__['LeftConditionChain'], out)
        out = self.__handleConditionChain(element.__dict__['RightConditionChain'], out)

        # Append operator
        cnt = len(out)
        if element.__dict__['Operator'] == "or":
            out[cnt + 1] = {'operator': get_operator('Or')()}
        else:
            out[cnt + 1] = {'operator': get_operator('And')()}

        return out

    def __handleCondition(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'Condition' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice->When->ConditionChain->Condition
        """

        # Get the condition name and the parameters to use.
        # The name of the condition specifies which ElementComparator
        # we schould use.
        name = element.__dict__['Name'].text
        params = []
        for entry in element.iterchildren():
            if entry.tag == "%sParam" % self.__namespace:
                params.append(entry.text)

        # Append the condition to the process list.
        cnt = len(out) + 1
        out[cnt] = {'condition': get_comparator(name)(), 'params': params}
        return out
