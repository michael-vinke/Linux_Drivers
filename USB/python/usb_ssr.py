#! /usr/bin/python3
#
# Copyright (c) 2018 Warren J. Jasper <wjasper@ncsu.edu>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import hid
import time

class usb_ssr:

  DIO_PORTC_LOW  = 0x2
  DIO_PORTC_HI   = 0x3
    
  # Commands and Codes for USB SSR24 and SSR 08  HID reports
  # Digital I/O Commands
  DIN              = 0x03 # Read digital port
  DOUT             = 0x04 # Write digital port
  DBIT_IN          = 0x05 # Read Digital port bit
  DBIT_OUT         = 0x06 # Write Digital port bit

  # Memory Commands
  MEM_READ         = 0x30 # Read Memory
  MEM_WRITE        = 0x31 # Write Memory

  # Miscellaneous Commands
  BLINK_LED        = 0x40 # Causes LED to blink
  RESET            = 0x41 # Reset USB interface
  GET_STATUS       = 0x44 # Retrieve device status
  GET_ALL          = 0x46 # Retrieve all digital input values

  PREPARE_DOWNLOAD = 0x50 # Prepare for program memory download
  WRITE_CODE       = 0x51 # Write program memory
  WRITE_SERIAL     = 0x53 # Write new serial number to device
  READ_CODE        = 0x55 # Read program memory

  productID        = 0

  def __init__(self):
    try:
      self.h = hid.device()
    except:
      print('USB-SSR: Error in creating hid device')
      return

  #################################
  #     Digital I/O  Commands     #
  #################################

  def DIn(self, port):
    # This command reads the digital port

    self.h.write([self.DIN, port])
    try:
      value = self.h.read(8,100)
    except:
      print('DIn: error in reading.')

    return value[0]

  def DOut(self, port, value):
    # This command writes data to the DIO port.
    self.h.write([self.DOUT, port, value])

  def DBitIn(self, port, bit):
    # Reads digital port bit
    self.h.write([0, self.DBIT_IN, port, bit])
    try:
      value = self.h.read(8,100)
    except:
      print('DBitIn: error in reading.')
    return value[0]

  def DBitOut(self, port, pin, value):
    # Writes digital port bit
    try:
      self.h.write([self.DBIT_OUT, port, pin, value])
    except:
      print('Error in DBitOut. port =',port,' bit =',bit,' value = ',value)

  #################################
  #     Memory  Commands          #
  #################################

  def MemRead(self, address, count):
    # This command reads data from the configuration memeory (EEPROM).
    if (count > 62):
      print('MemRead: max count is 62')
      return
    self.h.write([self.MEM_READ, address&0xff, (address >>8)&0xff, 0, count])
    try:
      value = self.h.read(count, 500)
    except:
      print('Error in reading memory, value =', value)
    return(value[0:count])

  def MemWrite(self, address, count, data):
    # This command writes data to the non-volatile EEPROM memory on the device.
    # The non-volatile memory is used to store calibration coefficients, system
    # information and user data.
    #    data:  the data to be written (59 bytes max)
    # Locations 0x00-0x7F are reserved for firmware and my not be written.

    if (count > 59):
      print('MemWrite: max count is 59')
      return
    if (address <= 0x7f):
      print('MemWrite: Locations 0x00-0x7F are reserved for firmware and my not be written.')
    self.h.write([self.MEM_Write, address & 0xff, (address>>8) & 0xff, count, data[0:count]])

  #################################
  #     Miscellaneous Commands    #
  #################################

  def Blink(self):
    # This commands causes the LED to flash several times.
    self.h.write([self.BLINK_LED])

  def Reset(self):
    # The command causes the device to perform a soft reset. The device
    # simulates a disconnect from the USB bus which in turn causes the
    # host computer to re-enumerate the device.
    self.h.write([self.RESET])

  def Status(self):
    # Bit 0: Port A direction setting      (0 = output,    1 = input)
    # Bit 1: Port B direction setting      (0 = output,    1 = input)
    # Bit 2: Port C Low direction setting  (0 = output,    1 = input)
    # Bit 3: Port C High direction setting (0 = output,    1 = input)
    # Bit 4: Port A polarity setting       (0 = inverted,  1 = normal)
    # Bit 5: Port B polarity setting       (0 = inverted,  1 = normal)
    # Bit 6: Port C Low polarity setting   (0 = inverted,  1 = normal)
    # Bit 7: Port C High polarity setting  (0 = inverted,  1 = normal)
    # Bit 8: Port A pull-up setting        (0 = pull down, 1 = pull up)
    # Bit 9: Port B pull-up setting        (0 = pull down, 1 = pull up)
    # Bit 10: Port C Low  pull-up setting  (0 = pull down, 1 = pull up)
    # Bit 11: Port C High pull-up setting  (0 = pull down, 1 = pull up)

    self.h.write([self.GET_STATUS])

    value = self.h.read(2, 1000)
    return (value[0] | (value[1]<<8))

  def GetALL(self):
    # Reads value from all digital I/O's
    # uint8_t Port_A
    # uint8_t Port_B
    # uint8_t Port_C_Low
    # uint8_t Port_C_High

    self.h.write([self.GET_ALL])
    value = self.h.read(4, 500)
    return (value[0:4])

  def PrepareDownload(self):
    # This command puts the device into code update mode.  The unlock code must be correct as a
    # further safety device.  Call this once before sending code with usbWriteCode.  If not in
    # code update mode, any usbWriteCode will be ignored.  A usbReset command must be issued at
    # the end of the code download in order to return the device to operation with the new code.

    self.h.write([self.PREPARE_DOWNLOAD, 0xad])

  def WriteCode(self, address, count, data):
    # This command writes to the program memory in the device.  This command is not accepted
    # unless the device is in update mode.  This command will normally be used when downloading
    # a new hex file, so it supports memory ranges that may be found in the hex file.  
    #
    # The address ranges are:
    #
    # 0x000000 - 0x007AFF:  Microcontroller FLASH program memory
    # 0x200000 - 0x200007:  ID memory (serial number is stored here on main micro)
    # 0x300000 - 0x30000F:  CONFIG memory (processor configuration data)
    # 0xF00000 - 0xF03FFF:  EEPROM memory
    #
    # FLASH program memory: The device must receive data in 64-byte segments that begin
    # on a 64-byte boundary.  The data is sent in messages containing 32 bytes.  count
    # must always equal 32.
    #
    # Other memory: Any number of bytes up to the maximum (32) may be sent.

    if (count > 32):
      print('WriteCode: count greater than 32')
      return
    self.h.write([self.WRITE_CODE, address&0xff, (address>>8)&0xff, (address>>16)&0xff, count, data[0:count]])

  def ReadCode(self, address, count):
    # This command reads from program memory.
    if (count > 62):
      print('ReadCode: count greater than 62')
      return
    self.h.write([self.h.read_CODE, address&0xff, (address>>8)&0xff, (address>>16)&0xff, count])
    value = self.h.read(count+1, 500)
    return (value[1,count+1])

  def WriteSerial(self, serial):
    # This command sends a new serial number to the device.  The serial number consists
    # of 8 bytes, typically ASCII numberic or hexadecimal digits (i.e. "00000001").
    # Note: The new serial number will be programmed but not used until hardware reset.
    self.h.write(self.WRITE_SERIAL,serial[0:8])

########################################################################################
                
class usb_ssr24(usb_ssr):
  DIO_PORTA      = 0x0
  DIO_PORTB      = 0x1

  def __init__(self, serial=None):
    usb_ssr.__init__(self)
    try:
      self.h.open(0x9db, 0x0085, serial)
    except:
      print('Can not open USB-SSR24')
      return

    self.productID = 0x0085                      #MCC USB-SSR24

    # enable non-blocking mode
    self.h.set_nonblocking(1)

class usb_ssr08(usb_ssr):
  def __init__(self, serial=None):
    usb_ssr.__init__(self)
    try:
      self.h.open(0x9db, 0x0086, serial)
    except:
      print('Can not open USB-SSR08')
      return

    self.productID = 0x0086                      #MCC USB-SSR08

    # enable non-blocking mode
    self.h.set_nonblocking(1)

  