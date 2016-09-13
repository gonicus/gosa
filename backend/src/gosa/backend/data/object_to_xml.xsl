<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:exslt="http://exslt.org/common"
    xmlns:g="http://www.gonicus.de/Objects"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

    <xsl:output method="xml" indent="yes" encoding="UTF-8" />

    <xsl:template match="/">

        <!-- Create some variables -->
        <xsl:variable name="class" select="/g:merge/g:class" />
        <xsl:variable name="props" select="/g:merge/g:properties/g:property" />
        <xsl:variable name="only_indexed" select="/g:merge/g:only_indexed/text()" />

        <!-- Create the 'Class' element -->
        <xsl:element name="{$class}" 
            xmlns="http://www.gonicus.de/Objects"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://www.gonicus.de/Objects objects.xsd"
            >
           
            <!-- Add namespace attributes --> 
            <xsl:attribute namespace="http://www.w3.org/2001/XMLSchema-instance"
                name="schemaLocation">http://www.gonicus.de/Objects objects.xsd</xsl:attribute>

            <!-- Add elements -->
    		<UUID><xsl:value-of select="$props[g:name='entry-uuid']/g:value/text()" /></UUID>
    		<Type><xsl:value-of select="$class" /></Type>
    		<DN><xsl:value-of select="$props[g:name='dn']/g:value/text()" /></DN>
    		<ParentDN><xsl:value-of select="$props[g:name='parent-dn']/g:value/text()" /></ParentDN>
    		<LastChanged><xsl:value-of select="$props[g:name='modify-date']/g:value/text()" /></LastChanged>

            <!-- Add Extensions -->
            <xsl:if test="/g:merge/g:extensions/g:extension">
                <Extensions>
                    <xsl:for-each select="/g:merge/g:extensions/g:extension">
                        <Extension><xsl:value-of select="." /></Extension>
                    </xsl:for-each>
                </Extensions>
            </xsl:if>

    		<!--
    		<AvailableExtensions>
    			<xsl:for-each select="/g:merge/g:defs/g:Objects/g:Object[g:Extends/g:Value=$class]">
    				<Extension>
    					<xsl:value-of select="g:Name" />
    				</Extension>
    			</xsl:for-each>
    		</AvailableExtensions>
    		<CanExtend>
    			<xsl:for-each select="/g:merge/g:defs/g:Objects/g:Object[g:Name=$class]/g:Extends">
    				<Extension>
    					<xsl:value-of select="g:Value" />
    				</Extension>
    			</xsl:for-each>
    		</CanExtend>
    		-->

            <!-- Copy container information for this object -->
            <xsl:value-of select="/g:merge/g:defs/g:Objects/g:Object[g:Name=$class]/g:Container/node()"/>
    
            <!-- Handle object attributes -->
            <Attributes>

                <!-- Combine all BaseObject-attributes with those of the ExtensionObjects -->
                <xsl:variable name="result">

                    <!-- Base-Object attributes --> 
                    <xsl:for-each select="/g:merge/g:defs/g:Objects/g:Object[g:Name = $class]/g:Attributes/g:Attribute">
                        <xsl:copy-of select="." />
                    </xsl:for-each>

                    <!-- Extension attributes --> 
    			    <xsl:for-each select="/g:merge/g:extensions">
                        <xsl:variable name="ext" select="g:extension" />
                        <xsl:for-each select="/g:merge/g:defs/g:Objects/g:Object[g:Name = $ext]/g:Attributes/g:Attribute">
                            <xsl:copy-of select="." />
                        </xsl:for-each>
                    </xsl:for-each>
                </xsl:variable>

                <!-- Append all collected attributes with their values -->
                <xsl:for-each select="exslt:node-set($result)/g:Attribute">

                    <!-- Sort by attribute name -->
                    <xsl:sort select="g:Name"/>

                    <!-- Jump over attributes, we've already seen 
                            1. Skip foreign attributes
                            2. Skip attributes we've already added.
                    -->
                    <xsl:if test="not(g:Name=preceding-sibling::g:Attribute/g:Name)">

                        <!-- Skip attributes that do not have to be indexed-->
                        <xsl:if test="($only_indexed='false')">
                            <xsl:variable name="propname" select="g:Name" />
                            <xsl:variable name="proptype" select="g:Type" />
                            <xsl:if test="$props[g:name=$propname]/g:value">
                               <xsl:for-each select="$props[g:name=$propname]">
                                           <xsl:for-each select="g:value">
                                    <xsl:if test="$proptype='Binary'">
                                        <xsl:element name="{$propname}">
                                            <xsl:attribute name="base64">true</xsl:attribute>
                                            <xsl:value-of select="." />
                                        </xsl:element>
                                    </xsl:if>
                                    <xsl:if test="not($proptype='Binary')">
                                        <xsl:element name="{$propname}"><xsl:value-of select="." /></xsl:element>
                                    </xsl:if>
                                </xsl:for-each>
                                </xsl:for-each>
                            </xsl:if>
                        </xsl:if>
                    </xsl:if>
                </xsl:for-each>
            </Attributes>
        </xsl:element>
    </xsl:template>
</xsl:stylesheet>
