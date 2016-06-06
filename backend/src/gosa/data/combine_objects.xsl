<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
	<xsl:output method="xml" indent="yes" encoding="UTF-8" />
	<xsl:template match="/">
		<Objects  xmlns="http://www.gonicus.de/Objects" 
			xmlns:o="http://www.gonicus.de/Objects">
			<xsl:for-each select="/o:Paths/o:Path">
	                        <xsl:variable name="path">
        	                        <xsl:value-of select="." />
                	        </xsl:variable>
				<xsl:for-each select="document($path)/o:Objects/o:Object">
					<xsl:copy>
						<xsl:apply-templates select="@*|node()" />
					</xsl:copy>
				</xsl:for-each>
			</xsl:for-each>
		</Objects>
	</xsl:template>
        <xsl:template match="@*|node()">
                <xsl:copy>
                        <xsl:apply-templates select="@*|node()" />
                </xsl:copy>
        </xsl:template>
</xsl:stylesheet>
