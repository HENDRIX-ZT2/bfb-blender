def srgb_to_lin(img32):
	mask = img32 >= 0.04045
	img32[mask] = ((img32[mask] + 0.055) / 1.055)**2.4
	img32[~mask] = img32[~mask] / 12.92
