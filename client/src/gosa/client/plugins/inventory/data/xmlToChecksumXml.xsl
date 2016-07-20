<xsl:stylesheet version="1.0"
	xmlns:e="http://www.gonicus.de/Events" 
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:strip-space elements="*"/>
	<xsl:output method="xml" indent="yes" encoding="UTF-8" />

	<xsl:template match="@*|node()">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()" />
		</xsl:copy>
	</xsl:template>
	<xsl:template match="/e:Event/e:Inventory/e:DeviceID"></xsl:template>
	<xsl:template match="/e:Event/e:Inventory/e:Checksum"></xsl:template>
	<xsl:template match="/e:Event/e:Inventory/e:HardwareUUID"></xsl:template>
	<xsl:template match="/e:Event/e:Inventory/e:AccessLog"></xsl:template>
	<xsl:template match="/e:Event/e:Inventory/e:USBDevice"></xsl:template>
	<xsl:template match="/e:Event/e:Inventory/e:Environment"></xsl:template>
	<xsl:template match="/e:Event/e:Inventory/e:Hardware/e:ReportGenerationTime"></xsl:template>
	<xsl:template match="/e:Event/e:Inventory/e:Hardware/e:ProcessorSpeed"></xsl:template>
	<xsl:template match="/e:Event/e:Inventory/e:Cpu/e:Speed"></xsl:template>
	<xsl:template match="/e:Event/e:Inventory/e:Hardware/e:Description"></xsl:template>
	<xsl:template match="/e:Event/e:Inventory/e:Hardware/e:UserID"></xsl:template>
	<xsl:template match="/e:Event/e:Inventory/e:Login"></xsl:template>
	<xsl:template match="/e:Event/e:Inventory/e:Drive/e:FreeSpace"></xsl:template>
</xsl:stylesheet>
