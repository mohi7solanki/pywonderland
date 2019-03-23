"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Real time animation of Wythoff construction with pyglet and glsl
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Code adapted from Matt Zucker's excellent shadertoy program at

    "https://www.shadertoy.com/view/Md3yRB"

This program has some rich features and a great UI (as a pure shader program!).

Some notes:

1. This program draws only a subset of all uniform polyhedron in 3d,
   it can't draw star and snub ones (the only exception is those with Schläfli
   symbol (3, 5/2), but you must change the code manually in the function
   `setup_triangle` in `common.frag` to see them.

2. The antialiasing routine in Matt's code is replaced by the usual supersampling
   method, it's slower than Matt's method but can give better result. Also I deleted
   some redundant code (for example the usage of iChannel1 in BufferA and BufferB)
   from Matt's program.

"""
import sys
sys.path.append("../glslhelpers")

import time
import argparse

import pyglet
pyglet.options["debug_gl"] = False
import pyglet.gl as gl
import pyglet.window.key as key

from shader import Shader
from framebuffer import FrameBuffer
from texture import create_image_texture


FONT_TEXTURE = "../glslhelpers/textures/font.png"


class Wythoff(pyglet.window.Window):

    def __init__(self, width, height, aa=1):
        """
        :param width and height: size of the window in pixels.

        :param aa: antialiasing level, a higher value will give better
            result but also slow down the animation. (AA=2 is recommended)
        """
        pyglet.window.Window.__init__(self,
                                      width,
                                      height,
                                      caption="Wythoff Explorer",
                                      resizable=True,
                                      visible=False,
                                      vsync=False)
        self._start_time = time.clock()
        self._frame_count = 0
        self._speed = 20
        self.aa = aa
        self.shaderA = Shader(["./glsl/wythoff.vert"], ["./glsl/common.frag",
                                                        "./glsl/BufferA.frag"])
        self.shaderB = Shader(["./glsl/wythoff.vert"], ["./glsl/common.frag",
                                                        "./glsl/BufferB.frag"])
        self.shaderC = Shader(["./glsl/wythoff.vert"], ["./glsl/common.frag",
                                                        "./glsl/main.frag"])
        self.font_texture = create_image_texture(FONT_TEXTURE)
        self.iChannel0 = pyglet.image.Texture.create_for_size(gl.GL_TEXTURE_2D, width, height,
                                                              gl.GL_RGBA32F_ARB)
        self.iChannel1 = pyglet.image.Texture.create_for_size(gl.GL_TEXTURE_2D, width, height,
                                                              gl.GL_RGBA32F_ARB)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(self.iChannel0.target, self.iChannel0.id)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(self.iChannel1.target, self.iChannel1.id)
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.font_texture)

        with FrameBuffer() as self.bufferA:
            self.bufferA.attach_texture(self.iChannel0)

        with FrameBuffer() as self.bufferB:
            self.bufferB.attach_texture(self.iChannel1)

        with self.shaderA:
            self.shaderA.vertex_attrib("position", [-1, -1, 1, -1, -1, 1, 1, 1])
            self.shaderA.uniformf("iResolution", width, height, 0.0)
            self.shaderA.uniformf("iTime", 0.0)
            self.shaderA.uniformf("iMouse", 0.0, 0.0, 0.0, 0.0)
            self.shaderA.uniformi("iChannel0", 0)
            self.shaderA.uniformi("iFrame", 0)

        with self.shaderB:
            self.shaderB.vertex_attrib("position", [-1, -1, 1, -1, -1, 1, 1, 1])
            self.shaderB.uniformf("iResolution", width, height, 0.0)
            self.shaderB.uniformf("iTime", 0.0)
            self.shaderB.uniformf("iMouse", 0.0, 0.0, 0.0, 0.0)
            self.shaderB.uniformi("iChannel0", 0)
            self.shaderB.uniformi("AA", self.aa)

        with self.shaderC:
            self.shaderC.vertex_attrib("position", [-1, -1, 1, -1, -1, 1, 1, 1])
            self.shaderC.uniformf("iResolution", width, height, 0.0)
            self.shaderC.uniformf("iTime", 0.0)
            self.shaderC.uniformf("iMouse", 0.0, 0.0, 0.0, 0.0)
            self.shaderC.uniformi("iChannel0", 0)
            self.shaderC.uniformi("iChannel1", 1)
            self.shaderC.uniformi("iTexture", 2)

    def on_draw(self):
        gl.glClearColor(0, 0, 0, 0)
        self.clear()
        gl.glViewport(0, 0, self.width, self.height)
        now = time.clock() - self._start_time
        now *= self._speed
        with self.bufferA:
            with self.shaderA:
                self.shaderA.uniformf("iTime", now)
                self.shaderA.uniformi("iFrame", self._frame_count)
                gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)

        with self.bufferB:
            with self.shaderB:
                self.shaderB.uniformf("iTime", now)
                gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)

        with self.shaderC:
            self.shaderC.uniformf("iTime", now)
            gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)

        self._frame_count += 1

    def on_key_press(self, symbol, modifiers):
        """Keyboard interface.
        """
        if symbol == key.ENTER:
            self.save_screenshot()

        if symbol == key.ESCAPE:
            pyglet.app.exit()

    def on_mouse_press(self, x, y, button, modifiers):
        with self.shaderA:
            self.shaderA.uniformf("iMouse", x, y, x, self.height - y)

        with self.shaderB:
            self.shaderB.uniformf("iMouse", x, y, x, self.height - y)

        with self.shaderC:
            self.shaderC.uniformf("iMouse", x, y, x, self.height - y)

    def on_mouse_release(self, x, y, button, modifiers):
        with self.shaderA:
            self.shaderA.uniformf("iMouse", 0, 0, 0, 0)

        with self.shaderB:
            self.shaderB.uniformf("iMouse", 0, 0, 0, 0)

        with self.shaderC:
            self.shaderC.uniformf("iMouse", 0, 0, 0, 0)

    def save_screenshot(self):
        with self.shaderB:
            image_buffer = pyglet.image.get_buffer_manager().get_color_buffer()
            image_buffer.save("screenshoot.png")

    def run(self, fps=None):
        self.set_visible(True)
        if fps is None:
            pyglet.clock.schedule(lambda dt: None)
        else:
            pyglet.clock.schedule_interval(lambda dt: None, 1.0/fps)
        pyglet.app.run()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-size", metavar="s", type=str,
                        default="800x480", help="window size in pixels")
    parser.add_argument("-qq", type=int, default=1,
                        help="antialiasing level")
    args = parser.parse_args()
    w, h = [int(x) for x in args.size.split("x")]
    app = Wythoff(width=w, height=h, aa=args.aa)
    app.run()


if __name__ == "__main__":
    main()