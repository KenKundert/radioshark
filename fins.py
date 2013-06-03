class Info():
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

# The following gives the address information for any fins you have.
# audioAddr:
#     Use 'arecord -l' to find the audioAddr (look for the device with the
#     RadioSHARK name. The format is 'hw:C,D' where C is the card number and D
#     is the device number.
# ctrlAddr:
#     The ctrlAddr should be set to 0 unless you have more than one fin. If you
#     have more than one fin, they will be named consecutively from 0. To
#     determine which ctrlAddr corresponds to each audioAddr, use arecord to
#     listen to a particular audioAddr while using the shark control program to
#     change the channel and change the color of the fin.
#     control program 
# This information is subject to change if you change the USB socket that the
# fin uses or if you reboot the machine.

fins = {
    'baseball': Info(audioAddr='hw:1,0', ctrlAddr='0'),
    'football': Info(audioAddr='hw:0,0', ctrlAddr='1')
}
