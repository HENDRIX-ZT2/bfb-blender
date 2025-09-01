def srgb_to_lin(img):
	mask = img >= 0.04045
	img[mask] = ((img[mask] + 0.055) / 1.055) ** 2.4
	img[~mask] = img[~mask] / 12.92

def lin_to_srgb(img):
	mask = img > 0.0031308
	img[mask] = 1.055 * (img ** (1.0 / 2.4)) - 0.055
	img[~mask] = 12.92 * img