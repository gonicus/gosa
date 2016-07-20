<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

	<xsl:output method="xml" indent="yes" encoding="UTF-8" />
	<xsl:template match="/">
		<Event  xmlns="http://www.gonicus.de/Events" 
			xmlns:e="http://www.gonicus.de/Events"
			xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
			xsi:schemaLocation="http://www.gonicus.de/Events ../../../../../../../agent/src/clacks/agent/plugins/goto/data/events/Inventory.xsd ">

			<Inventory>
				<Checksum>%%CHECKSUM%%</Checksum>
				<DeviceID><xsl:value-of select="/REQUEST/DEVICEID" /></DeviceID>
				<QueryType><xsl:value-of select="/REQUEST/QUERY" /></QueryType>
				<ClientVersion><xsl:value-of select="/REQUEST/CONTENT/VERSIONCLIENT" /></ClientVersion>
				<ClientUUID>%%CUUID%%</ClientUUID>
				<HardwareUUID>%%HWUUID%%</HardwareUUID>
				<Hostname><xsl:value-of select="/REQUEST/CONTENT/HARDWARE/NAME" /></Hostname>

				<xsl:for-each select="/REQUEST/CONTENT/CONTROLLERS">
					<Controller>
						<Name><xsl:value-of select="NAME" /></Name>
						<Type><xsl:value-of select="TYPE" /></Type>
						<Manufacturer><xsl:value-of select="MANUFACTURER" /></Manufacturer>
						<Driver><xsl:value-of select="DRIVER" /></Driver>
						<PCIClass><xsl:value-of select="PCICLASS" /></PCIClass>
						<PCIID><xsl:value-of select="PCIID" /></PCIID>
						<PCISlot><xsl:value-of select="PCISLOT" /></PCISlot>
					</Controller>
				</xsl:for-each>

				<xsl:for-each select="/REQUEST/CONTENT/MODEMS">
					<Modem>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
						<Name><xsl:value-of select="NAME" /></Name>
					</Modem>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/DRIVES">
					<Drive>
						<Device><xsl:value-of select="VOLUMN" /></Device>
						<MountPoint><xsl:value-of select="TYPE" /></MountPoint>
						<Filesystem><xsl:value-of select="FILESYSTEM" /></Filesystem>
						<Serial><xsl:value-of select="SERIAL" /></Serial>
						<Label><xsl:value-of select="LABEL" /></Label>
						<xsl:call-template name="FormatDate_CreateDate">
							<xsl:with-param name="DateTime" select="CREATEDATE"/>
						</xsl:call-template>
						<TotalSpace><xsl:value-of select="TOTAL" /></TotalSpace>
						<FreeSpace><xsl:value-of select="FREE" /></FreeSpace>
					</Drive>
				</xsl:for-each>

				<xsl:for-each select="/REQUEST/CONTENT/STORAGES">
					<Storage>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
                        <DiskSize>
                             <xsl:choose>
                                <xsl:when test="floor(DISKSIZE) = DISKSIZE">
                                    <xsl:value-of select="DISKSIZE"/>
                                </xsl:when>
                                <xsl:otherwise>0</xsl:otherwise>
                            </xsl:choose>
                        </DiskSize>
						<Firmware><xsl:value-of select="FIRMWARE" /></Firmware>
						<Manufacturer><xsl:value-of select="MANUFACTURER" /></Manufacturer>
						<Model><xsl:value-of select="MODEL" /></Model>
						<Name><xsl:value-of select="NAME" /></Name>
						<SCSI_CHID><xsl:value-of select="SCSI_CHID" /></SCSI_CHID>
						<SCSI_COID><xsl:value-of select="SCSI_COID" /></SCSI_COID>
						<SCSI_LUN><xsl:value-of select="SCSI_LUN" /></SCSI_LUN>
						<SCSI_UNID><xsl:value-of select="SCSI_UNID" /></SCSI_UNID>
						<Serial><xsl:value-of select="SERIALNUMBER" /></Serial>
						<Type><xsl:value-of select="TYPE" /></Type>
					</Storage>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/MEMORIES">
					<Memory>
                        <Capacity>
                            <xsl:choose>
                                <xsl:when test="floor(CAPACITY) = CAPACITY">
                                    <xsl:value-of select="CAPACITY"/>
                                </xsl:when>
                                <xsl:otherwise>0</xsl:otherwise>
                            </xsl:choose>
                        </Capacity>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
						<Caption><xsl:value-of select="CAPTION" /></Caption>
						<Speed><xsl:value-of select="SPEED" /></Speed>
						<Type><xsl:value-of select="TYPE" /></Type>
                        <NumberOfSlots>
                            <xsl:choose>
                                <xsl:when test="floor(NUMSLOTS) = NUMSLOTS">
                                    <xsl:value-of select="NUMSLOTS"/>
                                </xsl:when>
                                <xsl:otherwise>0</xsl:otherwise>
                            </xsl:choose>
                        </NumberOfSlots>
						<Serial><xsl:value-of select="SERIALNUMBER" /></Serial>
					</Memory>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/PORTS">
					<Port>
						<Caption><xsl:value-of select="CAPTION" /></Caption>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
						<Name><xsl:value-of select="NAME" /></Name>
						<Type><xsl:value-of select="TYPE" /></Type>
					</Port>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/SLOTS">
					<Slot>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
						<Designation><xsl:value-of select="DESIGNATION" /></Designation>
						<Name><xsl:value-of select="NAME" /></Name>
						<Status><xsl:value-of select="STATUS" /></Status>
					</Slot>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/SOFTWARES">
					<Software>
						<Name><xsl:value-of select="NAME" /></Name>
						<Type><xsl:value-of select="FROM" /></Type>
						<Version><xsl:value-of select="VERSION" /></Version>
						<Publisher><xsl:value-of select="PUBLISHER" /></Publisher>
						<InstallDate><xsl:value-of select="INSTALLDATE" /></InstallDate>
						<Comments><xsl:value-of select="COMMENTS" /></Comments>
                        <Size>
                             <xsl:choose>
                                <xsl:when test="floor(FILESIZE) = FILESIZE">
                                    <xsl:value-of select="FILESIZE"/>
                                </xsl:when>
                                <xsl:otherwise>0</xsl:otherwise>
                            </xsl:choose>
                        </Size>
						<Folder><xsl:value-of select="FOLDER" /></Folder>
					</Software>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/MONITORS">
					<Monitor>
						<EDID_Base64><xsl:value-of select="BASE64" /></EDID_Base64>
						<EDID_UUEncode><xsl:value-of select="UUENCODE" /></EDID_UUEncode>
						<Caption><xsl:value-of select="CAPTION" /></Caption>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
						<Manufacturer><xsl:value-of select="MANUFACTURER" /></Manufacturer>
						<Serial><xsl:value-of select="SERIALNUMBER" /></Serial>
					</Monitor>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/VIDEOS">
					<Video>
						<Name><xsl:value-of select="Name" /></Name>
						<Memory><xsl:value-of select="MEMORY" /></Memory>
						<Chipset><xsl:value-of select="CHIPSET" /></Chipset>
						<Resolution><xsl:value-of select="RESOLUTION" /></Resolution>
					</Video>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/SOUNDS">
					<Sound>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
						<Manufacturer><xsl:value-of select="MANUFACTURER" /></Manufacturer>
						<Name><xsl:value-of select="Name" /></Name>
					</Sound>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/NETWORKS">
					<Network>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
						<Driver><xsl:value-of select="DRIVER" /></Driver>
						<IpAddress><xsl:value-of select="IPADDRESS" /></IpAddress>
						<DhcpIp><xsl:value-of select="IPDHCP" /></DhcpIp>
						<GatewayIp><xsl:value-of select="IPGATEWAY" /></GatewayIp>
						<SubnetMask><xsl:value-of select="IPMASK" /></SubnetMask>
						<Subnet><xsl:value-of select="IPSUBNET" /></Subnet>
						<MacAddress><xsl:value-of select="MACADDR" /></MacAddress>
						<PCISlot><xsl:value-of select="PCISLOT" /></PCISlot>
						<Slaves><xsl:value-of select="SLAVES" /></Slaves>
						<Status><xsl:value-of select="STATUS" /></Status>
						<Type><xsl:value-of select="TYPE" /></Type>
						<VirtualDevice><xsl:value-of select="VIRTUALDEV" /></VirtualDevice>
					</Network>
				</xsl:for-each>

				<xsl:for-each select="/REQUEST/CONTENT/HARDWARE">
					<Hardware>
						<Name><xsl:value-of select="NAME" /></Name>
						<Architecture><xsl:value-of select="ARCHNAME" /></Architecture>
						<Checksum><xsl:value-of select="CHECKSUM" /></Checksum>
						<LastLoggedUser><xsl:value-of select="LASTLOGGEDUSER" /></LastLoggedUser>
						<DateLastLoggedUser><xsl:value-of select="DATELASTLOGGEDUSER" /></DateLastLoggedUser>
						<DefaultGateway><xsl:value-of select="DEFAULTGATEWAY" /></DefaultGateway>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
						<IpAddress><xsl:value-of select="IPADDR" /></IpAddress>
                        <Memory>
                             <xsl:choose>
                                <xsl:when test="floor(MEMORY) = MEMORY">
                                    <xsl:value-of select="MEMORY"/>
                                </xsl:when>
                                <xsl:otherwise>0</xsl:otherwise>
                            </xsl:choose>
                        </Memory>
						<OperatingSystemComment><xsl:value-of select="OSCOMMENTS" /></OperatingSystemComment>
						<OperatingSystem><xsl:value-of select="OSNAME" /></OperatingSystem>
						<OperatingSystemVersion><xsl:value-of select="OSVERSION" /></OperatingSystemVersion>
						<UserID><xsl:value-of select="USERID" /></UserID>
                        <Processors>
                            <xsl:choose>
                                <xsl:when test="floor(PROCESSORN) = PROCESSORN">
                                    <xsl:value-of select="PROCESSORN"/>
                                </xsl:when>
                                <xsl:otherwise>0</xsl:otherwise>
                            </xsl:choose>
                        </Processors>
						<ProcessorSpeed><xsl:value-of select="PROCESSORS" /></ProcessorSpeed>
						<ProcessorType><xsl:value-of select="PROCESSORT" /></ProcessorType>
                        <SwapMemory>
                            <xsl:choose>
                                <xsl:when test="floor(SWAP) = SWAP">
                                    <xsl:value-of select="SWAP"/>
                                </xsl:when>
                                <xsl:otherwise>0</xsl:otherwise>
                            </xsl:choose>
                        </SwapMemory>
						<VirtualMachineSystem><xsl:value-of select="VMSYSTEM" /></VirtualMachineSystem>
						<Workgroup><xsl:value-of select="WORKGROUP" /></Workgroup>
						<DNS><xsl:value-of select="DNS" /></DNS>
                        <ReportGenerationTime>
                            <xsl:choose>
                                <xsl:when test="floor(ETIME) = ETIME">
                                    <xsl:value-of select="ETIME"/>
                                </xsl:when>
                                <xsl:otherwise>0</xsl:otherwise>
                            </xsl:choose>
                        </ReportGenerationTime>
						<Type><xsl:value-of select="TYPE" /></Type>
					</Hardware>
				</xsl:for-each>

				<xsl:for-each select="/REQUEST/CONTENT/BIOS">
					<Bios>
						<BiosDate><xsl:value-of select="BDATE" /></BiosDate>
						<BiosManufacturer><xsl:value-of select="BMANUFACTURER" /></BiosManufacturer>
						<BiosVersion><xsl:value-of select="BVERSION" /></BiosVersion>
						<SystenManufacturer><xsl:value-of select="SMANUFACTURER" /></SystenManufacturer>
						<SystemModel><xsl:value-of select="SMODEL" /></SystemModel>
						<SystemSerial><xsl:value-of select="SSN" /></SystemSerial>
						<BiosAssetTag><xsl:value-of select="ASSETTAG" /></BiosAssetTag>

						<!-- These tags seem to unused right now
						<MMANUFACTURER><xsl:value-of select="MMANUFACTURER" /></MMANUFACTURER>
						<MSN><xsl:value-of select="MSN" /></MSN>
						<MMODEL><xsl:value-of select="MMODEL" /></MMODEL>
						-->
					</Bios>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/CPUS">
					<Cpu>
						<Manufacturer><xsl:value-of select="MANUFACTURER" /></Manufacturer>
						<Type><xsl:value-of select="TYPE" /></Type>
						<Core><xsl:value-of select="CORE" /></Core>
                        <Speed>
                            <xsl:choose>
                                <xsl:when test="floor(SPEED) = SPEED">
                                    <xsl:value-of select="SPEED"/>
                                </xsl:when>
                                <xsl:otherwise>0</xsl:otherwise>
                            </xsl:choose>
                        </Speed>
						<Serial><xsl:value-of select="SERIAL" /></Serial>
						<Thread><xsl:value-of select="THREAD" /></Thread>
					</Cpu>
				</xsl:for-each>

				<xsl:for-each select="/REQUEST/CONTENT/USERS">
					<Login>
						<Login><xsl:value-of select="LOGIN" /></Login>
					</Login>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/PRINTERS">
					<Printer>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
						<Driver><xsl:value-of select="DRIVER" /></Driver>
						<Name><xsl:value-of select="NAME" /></Name>
						<Port><xsl:value-of select="PORT" /></Port>
					</Printer>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/VIRTUALMACHINES">
					<VirtualMachine>
						<Memory><xsl:value-of select="MEMORY" /></Memory>
						<Name><xsl:value-of select="NAME" /></Name>
						<UUID><xsl:value-of select="UUID" /></UUID>
						<Status><xsl:value-of select="STATUS" /></Status>
						<SubSystem><xsl:value-of select="SUBSYSTEM" /></SubSystem>
						<Type><xsl:value-of select="VMTYPE" /></Type>
						<CPUs><xsl:value-of select="VCPU" /></CPUs>
						<VirtualMachineID><xsl:value-of select="VMID" /></VirtualMachineID>
					</VirtualMachine>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/ACCESSLOG">
					<AccessLog>
						<xsl:call-template name="FormatDate_LoginDate">
							<xsl:with-param name="DateTime" select="LOGDATE"/>
						</xsl:call-template>
						<UserID><xsl:value-of select="USERID" /></UserID>
					</AccessLog>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/ENVS">
					<Environment>
						<Name><xsl:value-of select="KEY" /></Name>
						<Value><xsl:value-of select="VAL" /></Value>
					</Environment>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/USBDEVICES">
					<USBDevice>
						<Name><xsl:value-of select="NAME" /></Name>
						<VendorID><xsl:value-of select="VENDORID" /></VendorID>
						<ProductID><xsl:value-of select="PRODUCTID" /></ProductID>
						<Serial><xsl:value-of select="SERIAL" /></Serial>
						<Class><xsl:value-of select="CLASS" /></Class>
						<SubClass><xsl:value-of select="SUBCLASS" /></SubClass>
					</USBDevice>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/BATTERIES">
					<Battery>
						<Name><xsl:value-of select="NAME" /></Name>
						<Serial><xsl:value-of select="SERIAL" /></Serial>
						<Manufacturer><xsl:value-of select="MANUFACTURER" /></Manufacturer>
						<Voltage><xsl:value-of select="VOLTAGE" /></Voltage>
						<Date><xsl:value-of select="DATE" /></Date>
						<Chemistry><xsl:value-of select="CHEMISTRY" /></Chemistry>
						<Capacity><xsl:value-of select="CAPACITY" /></Capacity>
					</Battery>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/ANTIVIRUS">
					<Antivirus>
						<Company><xsl:value-of select="COMPANY" /></Company>
						<Name><xsl:value-of select="NAME" /></Name>
						<GUID><xsl:value-of select="GUID" /></GUID>
						<Enabled><xsl:value-of select="ENABLED" /></Enabled>
						<UpToDate><xsl:value-of select="UPTODATE" /></UpToDate>
						<Version><xsl:value-of select="VERSION" /></Version>
					</Antivirus>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/LOGICAL_VOLUMES">
					<LogicalVolume>
						<Name><xsl:value-of select="LV_NAME" /></Name>
						<UUID><xsl:value-of select="LV_UUID" /></UUID>
						<VolumeGroupName><xsl:value-of select="VG_NAME" /></VolumeGroupName>
						<Parameters><xsl:value-of select="ATTR" /></Parameters>
						<Size><xsl:value-of select="SIZE" /></Size>
						<SegmentCount><xsl:value-of select="SEG_COUNT" /></SegmentCount>
					</LogicalVolume>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/PHYSICAL_VOLUMES">
					<PhysicalVolume>
						<Device><xsl:value-of select="DEVICE" /></Device>
						<Name><xsl:value-of select="PV_NAME" /></Name>
						<UUID><xsl:value-of select="PV_UUID" /></UUID>
						<Format><xsl:value-of select="FORMAT" /></Format>
						<Parameters><xsl:value-of select="ATTR" /></Parameters>
						<Size><xsl:value-of select="SIZE" /></Size>
						<Free><xsl:value-of select="FREE" /></Free>
						<ExtendSize><xsl:value-of select="PE_SIZE" /></ExtendSize>
						<ExtendCount><xsl:value-of select="PV_PE_COUNT" /></ExtendCount>
					</PhysicalVolume>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/VOLUME_GROUPS">
					<VolumeGroup>
						<Name><xsl:value-of select="VG_NAME" /></Name>
						<PhysicalVolumeCount><xsl:value-of select="PV_COUNT" /></PhysicalVolumeCount>
						<LogicalVolumeCount><xsl:value-of select="LV_COUNT" /></LogicalVolumeCount>
						<Parameters><xsl:value-of select="ATTR" /></Parameters>
						<Size><xsl:value-of select="SIZE" /></Size>
						<Free><xsl:value-of select="FREE" /></Free>
						<UUID><xsl:value-of select="VG_UUID" /></UUID>
						<ExtendSize><xsl:value-of select="VG_EXTENT_SIZE" /></ExtendSize>
					</VolumeGroup>
				</xsl:for-each> 
			</Inventory>
		</Event>
	</xsl:template>

	<!-- Converts  <<2011-10-9 07:20>> to <<2002-10-10T17:00:00Z>> -->
	<xsl:template name="FormatDate_LoginDate">
		<xsl:param name="DateTime" />

		<!-- If the value is empty, then create a 'nil' statement -->
		<xsl:if test="(string-length($DateTime) = 0)">
			<xsl:element name="LoginDate" namespace="http://www.gonicus.de/Events">
				<xsl:attribute name="nil" namespace="http://www.w3.org/2001/XMLSchema-instance">true</xsl:attribute>
			</xsl:element>
		</xsl:if>

		<!-- If the value is NOT empty, then create a valid xs:dateTime statement -->
		<xsl:if test="(string-length($DateTime) != 0)">

			<xsl:variable name="year">
				<xsl:value-of select="substring($DateTime,1,4)" />
			</xsl:variable>

			<xsl:variable name="month-temp">
				<xsl:value-of select="substring-after($DateTime,'-')" />
			</xsl:variable>
			<xsl:variable name="month">
				<xsl:value-of select="substring-before($month-temp,'-')" />
			</xsl:variable>

			<xsl:variable name="day-temp">
				<xsl:value-of select="substring-after($month-temp,'-')" />
			</xsl:variable>
			<xsl:variable name="day">
				<xsl:value-of select="substring-before($day-temp,' ')" />
			</xsl:variable>
			<xsl:variable name="time">
				<xsl:value-of select="substring-after($day-temp,' ')" />
			</xsl:variable>

			<xsl:element name="LoginDate" namespace="http://www.gonicus.de/Events">
				<xsl:value-of select="$year"/>
				<xsl:value-of select="'-'"/>

				<xsl:if test="(string-length($month) &lt; 2)">
					<xsl:value-of select="0"/>
				</xsl:if>
				<xsl:value-of select="$month"/>
				<xsl:value-of select="'-'"/>
				<xsl:if test="(string-length($day) &lt; 2)">
					<xsl:value-of select="0"/>
				</xsl:if>
				<xsl:value-of select="$day"/>
				<xsl:value-of select="'T'"/>
				<xsl:value-of select="$time"/>
				<xsl:value-of select="'Z'"/>
			</xsl:element>
		</xsl:if>
	</xsl:template>

	<!-- Converts  <<2011/3/1 14:36:06>> to <<2002-10-10T17:00:00Z>> -->
	<xsl:template name="FormatDate_CreateDate">
		<xsl:param name="DateTime" />

		<!-- If the value is empty, then create a 'nil' statement -->
		<xsl:if test="(string-length($DateTime) = 0)">
			<xsl:element name="CreateDate" namespace="http://www.gonicus.de/Events">
				<xsl:attribute name="nil" namespace="http://www.w3.org/2001/XMLSchema-instance">true</xsl:attribute>
			</xsl:element>
		</xsl:if>

		<!-- If the value is NOT empty, then create a valid xs:dateTime statement -->
		<xsl:if test="(string-length($DateTime) != 0)">
			<xsl:variable name="year">
				<xsl:value-of select="substring($DateTime,1,4)" />
			</xsl:variable>

			<xsl:variable name="month-temp">
				<xsl:value-of select="substring-after($DateTime,'/')" />
			</xsl:variable>
			<xsl:variable name="month">
				<xsl:value-of select="substring-before($month-temp,'/')" />
			</xsl:variable>

			<xsl:variable name="day-temp">
				<xsl:value-of select="substring-after($month-temp,'/')" />
			</xsl:variable>
			<xsl:variable name="day">
				<xsl:value-of select="substring-before($day-temp,' ')" />
			</xsl:variable>
			<xsl:variable name="time">
				<xsl:value-of select="substring-after($day-temp,' ')" />
			</xsl:variable>

			<xsl:element name="CreateDate" namespace="http://www.gonicus.de/Events">
				<xsl:value-of select="$year"/>
				<xsl:value-of select="'-'"/>

				<xsl:if test="(string-length($month) &lt; 2)">
					<xsl:value-of select="0"/>
				</xsl:if>
				<xsl:value-of select="$month"/>
				<xsl:value-of select="'-'"/>
				<xsl:if test="(string-length($day) &lt; 2)">
					<xsl:value-of select="0"/>
				</xsl:if>
				<xsl:value-of select="$day"/>
				<xsl:value-of select="'T'"/>
				<xsl:value-of select="$time"/>
				<xsl:value-of select="'Z'"/>
			</xsl:element>
		</xsl:if>
	</xsl:template>

</xsl:stylesheet>
