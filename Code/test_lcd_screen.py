# to run with python 3
#
import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as char_lcd
import time
from Src.Management import load_pattern



cols = 16
rows = 2

i2c = busio.I2C(board.SCL, board.SDA)
lcd = char_lcd.Character_LCD_RGB_I2C(i2c, cols, rows)

#print(board.SCL)
#print(board.SDA)

lcd.clear()
lcd.color = [100, 0, 0]

lcd.message = "Hello\nWorld!"

print('start ...')


for name in load_pattern.get_csv_files():
    print(name)


print(load_pattern.read_list_from_csv(
        load_pattern.get_local_dir() + '/' + name))


try:
	while True:
		if lcd.up_button:
			print('UP')
			lcd.clear()
			lcd.message = "UP"
		if lcd.right_button:
			print('RIGHT')
			lcd.clear()
			lcd.message = "RIGHT"
		if lcd.select_button:
			print('SELECT')
			lcd.clear()
			lcd.message = "SELECT"
		if lcd.down_button:
			print("DOWN")
			lcd.clear()
			lcd.message = "DOWN"
		if lcd.left_button:
			print("LEFT")
			lcd.clear()
			lcd.message = "LEFT"
		time.sleep(.3)
finally:
	lcd.clear()
	lcd.color = [0, 0, 0]

