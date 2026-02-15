// QuakeFall custom shaders

titanDebug
{
	nopicmip
	nomipmaps
	cull none
	{
		map $whiteimage
		rgbGen vertex
		alphaGen vertex
		blendFunc GL_SRC_ALPHA GL_ONE_MINUS_SRC_ALPHA
		depthWrite
	}
}
