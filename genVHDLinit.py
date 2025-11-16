"""
Created on Thu May  6 13:41:36 2021

@author: qubit-starman
"""

import sys
from pprint import pprint

if len(sys.argv) < 3:
    raise Exception('Pleae provide input and output file, like genVHDLinit.py <Si5338-Registers.h> <Si5338_BRAM.vhd>')

CBPRO_HEADER_PATH = sys.argv[1]
GEN_FILE_PATH = sys.argv[2]

rF = open(CBPRO_HEADER_PATH, "r")

address = []
regVal = []
regMask = []

num_regs_max = None
reg_data_active = False

while True:
    chunks = []
    line = rF.readline()

    if line == "//End of file\n":
        break

    if line.startswith("//"):
        print(f"SKIP '{line.strip()}'")
        continue

    elif len(line.strip()) == 0:
        print(f"SKIP '{line.strip()}'")
        continue

    elif line.startswith("#define NUM_REGS_MAX"):
        num_regs_max = line.strip().split(' ')[-1]
        print(' > num_regs_max:', num_regs_max)
        continue

    elif line.startswith("Reg_Data const code Reg_Store[NUM_REGS_MAX] = {"):
        print(f"reg_data_start '{line.strip()}'")
        reg_data_active = True
        continue


    if reg_data_active is True:
        if "// set page bit to" in line:
            line = line[:line.find("// set page bit to")]
        
        line = line.replace('},', '').replace('}', '').replace('{', '').replace(';', '').rstrip('\n')
        address_i, regVal_i, regMask_i = line.split(',')

        if address_i == "255":
            regVal_i = regVal_i.replace(" 1", "01").replace(" 0", "00")

        address.append(address_i)
        regVal.append(regVal_i.replace('0x', '').strip())
        regMask.append(regMask_i.replace('0x', '').strip())

        if "};" in line:
            print(f"reg_data_end '{line.strip()}'")
            reg_data_active = False

    else:
        print(f"IGNORE '{line.strip()}'")
    

rF.close()
wF = open(GEN_FILE_PATH, "w")

wF.write('''
library IEEE;
    use IEEE.STD_LOGIC_1164.ALL;
    use IEEE.NUMERIC_STD.ALL;


entity Si5338_init_bram is
  Port (
    
    
    clk : in STD_LOGIC; -- Clk in
    reset : in STD_LOGIC; -- reset in
    bram_addr : in std_logic_vector(8 downto 0); -- address in
    
    regData : out std_logic_vector(7 downto 0); -- register data for Si5338
    regMask : out std_logic_vector(7 downto 0); -- register mask for Si5338
    regAddr : out std_logic_vector(7 downto 0); -- register address for SI5338

    bram_entries : out std_logic_vector(9 downto 0) -- Number of entries in BRAM for transaction counter
  );
end Si5338_init_bram;

architecture Behavioral of Si5338_init_bram is

attribute mark_debug : string; 


constant max_entries_bram : integer range 0 to 350 := 348;
''')


wF.write("type i2c_bram is array (0 to " + str(len(regVal) - 1) + ") of std_logic_vector(7 downto 0); \r\n")
wF.write("type i2c_addr is array (0 to " + str(len(address) - 1) + ") of integer range 0 to " + address[len(address) - 1] + ";\n")
wF.write("type i2c_mask is array (0 to " + str(len(regMask) - 1) + ") of std_logic_vector(7 downto 0); \r\n")


wF.write('''
signal regData_i : std_logic_vector(7 downto 0);
attribute mark_debug of regData_i : signal is "true";

signal regMask_i : std_logic_vector(7 downto 0);
attribute mark_debug of regMask_i : signal is "true";

signal regAddr_i : std_logic_vector(7 downto 0);
attribute mark_debug of regAddr_i : signal is "true";

signal bram_addr_i : std_logic_vector(8 downto 0);
attribute mark_debug of bram_addr_i : signal is "true";
''')


wF.write("constant si5338_init_data : i2c_bram := ( \n")



for i in range(len(regVal)):
    #wF.write
    wF.write('x"' + regVal[i] + '"')
    if(i != (len(regVal)-1)):
       wF.write(',')
    if (i+1) % 8 == 0:
        wF.write("\n")

wF.write(");\n\n")
   
wF.write("constant si5338_init_addr : i2c_addr := ( \n")

print(len(address))

for i in range(len(address)):
    #wF.write
    wF.write(f"{address[i]:3s}")
    if(i != (len(address)-1)):
       wF.write(',')
    if (i+1) % 8 == 0:
        wF.write("\n")

wF.write(");\n\n")

wF.write("constant si5338_init_regMask : i2c_mask := ( \n")

for i in range(len(regMask)):
    #wF.write
    wF.write( 'x"' + regMask[i] + '"')
    if(i != (len(regMask)-1)):
       wF.write(',')
    if (i+1) % 8 == 0:
        wF.write("\n")

wF.write(");")


wF.write('''
begin

bram_entries <= std_logic_vector(to_unsigned(max_entries_bram, 10));
bram_addr_i <= bram_addr;

process(clk, reset)
begin

    if rising_edge(clk) then
    
        if reset = '1' then
            regData_i <= (others=>'0');
            regMask_i <= (others=>'0');
            regAddr_i <= (others=>'0');
        else
            if(to_integer(unsigned(bram_addr)) <= max_entries_bram) then
                regData_i <= si5338_init_data(to_integer(unsigned(bram_addr)));
                regMask_i <= si5338_init_regMask(to_integer(unsigned(bram_addr)));
                regAddr_i <= std_logic_vector(to_unsigned(si5338_init_addr(to_integer(unsigned(bram_addr))), 8));        
            else
                regData_i <= (others=>'0');
                regMask_i <= (others=>'1');
                regAddr_i <= (others=>'0');
            end if;                
        end if;    
    end if;

end process;

regData <= regData_i;
regMask <= regMask_i;
regAddr <= regAddr_i;


end Behavioral;
''')
    
    
wF.close()

    #break
#wF = open(genFileName, "w")
