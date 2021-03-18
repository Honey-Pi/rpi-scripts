function Decoder(bytes, port) {
  // Decode an uplink message from a buffer
  // (array) of bytes to an object of fields.
  var decoded = {};
  var converted = {};
  //console.log(bytes);
  // temperature 
 
      decoded.field1     =  (bytes[0]  << 16) + (bytes[1] << 8) + bytes[2];
      decoded.field2     =  (bytes[3]  << 16) + (bytes[4] << 8) + bytes[5];
      decoded.field3   =  (bytes[6]  << 16) + (bytes[7] << 8) + bytes[8];
      decoded.field4   =  (bytes[9]  << 16) + (bytes[10] << 8) + bytes[11];
      decoded.field5   =  (bytes[12]  << 16) + (bytes[13] << 8) + bytes[14];
      decoded.field6    =  (bytes[15]  << 16) + (bytes[16] << 8) + bytes[17];
      decoded.field7 =  (bytes[18]  << 16) + (bytes[19] << 8) + bytes[20];
      decoded.field8 =  (bytes[21]  << 16) + (bytes[22] << 8) + bytes[23];
  
  converted.field1 = decoded.field1 / 100;
  converted.field2 = decoded.field2 / 100;
  converted.field3 = decoded.field3 / 100;
  converted.field4 = decoded.field4 / 100;
  converted.field5 = decoded.field5 / 100;
  converted.field6 = decoded.field6 / 100;
  converted.field7 = decoded.field7 / 100;
  converted.field8 = decoded.field8 / 100;
  converted.api_key = "THGNLEBHE8UY0C44"
  // humidity 
  
  return converted;
}
 
function sflt162f(rawSflt16)
	{
	// rawSflt16 is the 2-byte number decoded from wherever;
	// it's in range 0..0xFFFF
	// bit 15 is the sign bit
	// bits 14..11 are the exponent
	// bits 10..0 are the the mantissa. Unlike IEEE format, 
	// 	the msb is transmitted; this means that numbers
	//	might not be normalized, but makes coding for
	//	underflow easier.
	// As with IEEE format, negative zero is possible, so
	// we special-case that in hopes that JavaScript will
	// also cooperate.
	//
	// The result is a number in the open interval (-1.0, 1.0);
	// 
	
	// throw away high bits for repeatability.
	rawSflt16 &= 0xFFFF;
 
	// special case minus zero:
	if (rawSflt16 == 0x8000)
		return -0.0;
 
	// extract the sign.
	var sSign = ((rawSflt16 & 0x8000) != 0) ? -1 : 1;
	
	// extract the exponent
	var exp1 = (rawSflt16 >> 11) & 0xF;
 
	// extract the "mantissa" (the fractional part)
	var mant1 = (rawSflt16 & 0x7FF) / 2048.0;
 
	// convert back to a floating point number. We hope 
	// that Math.pow(2, k) is handled efficiently by
	// the JS interpreter! If this is time critical code,
	// you can replace by a suitable shift and divide.
	var f_unscaled = sSign * mant1 * Math.pow(2, exp1 - 15);
 
	return f_unscaled;
	}