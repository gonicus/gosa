<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exslt="http://exslt.org/common"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <xsl:output method="xml" indent="yes" encoding="UTF-8" />
  <xsl:template match="/">
    <!-- Add an xsd:element which then points the later created object-type -->
    <!-- #TODO Check why we-ve to define namespaces twice -->
    <xsd:schema 
      xmlns="http://www.gonicus.de/Objects" 
      xmlns:g="http://www.gonicus.de/Objects" 
      targetNamespace="http://www.gonicus.de/Objects"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xmlns:xsd="http://www.w3.org/2001/XMLSchema"
      elementFormDefault="qualified">

      <!-- Add the base elements, each represents a valid object -->
      <xsl:for-each select="/g:Objects/g:Object[g:BaseObject='true']">
        <xsl:sort select="g:Name"/>
        <xsl:variable name="classname" select="g:Name" />
        <xsd:element name="{$classname}" type="{$classname}" />
      </xsl:for-each>

      <!-- We only need schema definitions for BaseObjects cause extensions cannot be exported without a base object. --> 
      <xsl:for-each select="/g:Objects/g:Object[g:BaseObject='true']">

        <!-- Sort classes by their name -->
        <xsl:sort select="g:Name"/>

        <xsl:variable name="classname" select="g:Name" />

        <!-- Combine all BaseObject-attributes with those of the ExtensionObjects -->
        <xsl:variable name="all_attrs">

          <!-- Base-Object properties -->
          <xsl:for-each select="g:Attributes/g:Attribute">
            <xsl:copy-of select="." />
          </xsl:for-each>
	  <xsl:for-each select="/g:Objects/g:Object[g:Extends/g:Value=$classname]/g:Attributes/g:Attribute">
            <xsl:copy-of select="." />
          </xsl:for-each>
        </xsl:variable>

        <!-- Create the complex type definition for the current class -->
        <xsd:complexType name="{$classname}">
          <xsd:sequence>

            <!-- Add the basic elements, required in all objects. -->
            <xsd:element type="xsd:string" name="UUID" minOccurs="1" maxOccurs="1"></xsd:element>
            <xsd:element type="xsd:string" name="Type" minOccurs="1" maxOccurs="1"></xsd:element>
            <xsd:element type="xsd:string" name="DN" minOccurs="1" maxOccurs="1"></xsd:element>
            <xsd:element type="xsd:string" name="ParentDN" minOccurs="1" maxOccurs="1"></xsd:element>
            <xsd:element type="xsd:dateTime" name="LastChanged" minOccurs="1" maxOccurs="1"></xsd:element>
            <xsd:element type="Extensions" name="Extensions" minOccurs="0" maxOccurs="1"></xsd:element>
            <xsd:element type="Container" name="Container" minOccurs="0" maxOccurs="1"></xsd:element>

            <!-- Add object attributes, including those from extensions -->
            <xsd:element name="Attributes" >
              <xsd:complexType>
                <xsd:sequence>

                  <!-- Add list of allowed attributes for this object -->
                  <xsl:for-each select="exslt:node-set($all_attrs)/g:Attribute">

                    <!-- Sort attributes by their name -->
                    <xsl:sort select="g:Name"/>

                    <!-- Convert Type-Strings used by clacks into xsd:types To allow a more detailed validation -->
                    <xsl:variable name="type">
                      <xsl:choose>
                        <xsl:when test="g:Type='String'">xsd:string</xsl:when>
                        <xsl:when test="g:Type='Integer'">xsd:integer</xsl:when>
                        <xsl:when test="g:Type='Boolean'">xsd:boolean</xsl:when>
                        <xsl:when test="g:Type='Timestamp'">xsd:dateTime</xsl:when>
                        <xsl:when test="g:Type='Date'">xsd:date</xsl:when>
                        <xsl:otherwise>xsd:string</xsl:otherwise>
                      </xsl:choose>
                    </xsl:variable>

                    <!-- Add an element describing the attribute --> 
                    <xsl:element name="xsd:element">
                      <xsl:attribute name="name"><xsl:value-of select="g:Name" /></xsl:attribute>
                      <xsl:attribute name="minOccurs">0</xsl:attribute>
                      <xsl:attribute name="maxOccurs">unbounded</xsl:attribute>
                      <xsl:if test="g:Type='Binary'">
                        <xsd:complexType>
                          <xsd:simpleContent>
                            <xsd:extension base="xsd:string">
                              <xsd:attribute name="base64" type="xsd:boolean"></xsd:attribute>
                            </xsd:extension>
                          </xsd:simpleContent>
                        </xsd:complexType>
                      </xsl:if>
                    </xsl:element>
                  </xsl:for-each>
                </xsd:sequence>
              </xsd:complexType>
            </xsd:element>

          </xsd:sequence>
        </xsd:complexType>
      </xsl:for-each>

      <!-- An xsd:complexType which represents the <Container> sequence -->
      <xsd:complexType name="Container">
        <xsd:sequence>
          <xsd:element type="xsd:string" name="Type" 
            minOccurs="1" maxOccurs="unbounded"></xsd:element>
        </xsd:sequence>
      </xsd:complexType>

      <!-- An xsd:complexType which represents the <Exstensions> sequence -->
      <xsd:complexType name="Extensions">
        <xsd:sequence>
          <xsd:element type="xsd:string" name="Extension" 
            minOccurs="1" maxOccurs="unbounded"></xsd:element>
        </xsd:sequence>
      </xsd:complexType>
    </xsd:schema>
  </xsl:template>
</xsl:stylesheet>
