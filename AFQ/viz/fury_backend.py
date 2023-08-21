import tempfile
import os.path as op
import logging

import numpy as np

import AFQ.viz.utils as vut

from dipy.tracking.streamline import set_number_of_points

try:
    from dipy.viz import window, actor, ui
    from fury.colormap import line_colors
    import IPython.display as display
except (ImportError, ModuleNotFoundError):
    raise ImportError(vut.viz_import_msg_error("fury"))

viz_logger = logging.getLogger("AFQ")


def _inline_interact(scene, inline, interact):
    """
    Helper function to reuse across viz functions
    """
    if interact:
        viz_logger.info("Showing interactive scene...")
        window.show(scene)

    if inline:
        viz_logger.info("Showing inline scene...")
        tdir = tempfile.gettempdir()
        fname = op.join(tdir, "fig.png")
        window.snapshot(scene, fname=fname, size=(1200, 1200))
        display.display_png(display.Image(fname))

    return scene


def visualize_bundles(sft, n_points=None, bundle_dict=None,
                      bundle=None, colors=None,
                      color_by_direction=False,
                      opacity=1.0,
                      flip_axes=[False, False, False],
                      figure=None, background=(1, 1, 1), interact=False,
                      inline=False, **kwargs):
    """
    Visualize bundles in 3D using VTK.
    Parameters not described below are extras to conform fury and plotly APIs.

    Parameters
    ----------
    sft : Stateful Tractogram, str
        A Stateful Tractogram containing streamline information
        or a path to a trk file
        In order to visualize individual bundles, the Stateful Tractogram
        must contain a bundle key in it's data_per_streamline which is a list
        of bundle `'uid'`.

    n_points : int or None
        n_points to resample streamlines to before plotting. If None, no
        resampling is done.

    bundle_dict : dict, optional
        Keys are names of bundles and values are dicts that specify them.
        Default: bundles are either not identified, or identified
        only as unique integers in the metadata.

    bundle : str or int, optional
        The name of a bundle to select from among the keys in `bundle_dict`
        or an integer for selection from the sft metadata.

    colors : dict or list
        If this is a dict, keys are bundle names and values are RGB tuples.
        If this is a list, each item is an RGB tuple. Defaults to a list
        with Tableau 20 RGB values if bundle_dict is None, or dict from
        bundles to Tableau 20 RGB values if bundle_dict is not None.

    color_by_direction : bool
        Whether to color by direction instead of by bundle. Default: False

    opacity : float
        Float between 0 and 1 defining the opacity of the bundle.
        Default: 1.0

    background : tuple, optional
        RGB values for the background. Default: (1, 1, 1), which is white
        background.

    figure : fury Scene object, optional
        If provided, the visualization will be added to this Scene. Default:
        Initialize a new Scene.

    interact : bool
        Whether to provide an interactive VTK window for interaction.
        Default: False

    inline : bool
        Whether to embed the visualization inline in a notebook. Only works
        in the notebook context. Default: False.

    Returns
    -------
    Fury Scene object
    """

    if figure is None:
        figure = window.Scene()

    figure.SetBackground(background[0], background[1], background[2])

    for (sls, color, name, dimensions) in vut.tract_generator(
            sft, bundle, bundle_dict, colors, n_points):
        sls = list(sls)
        if name == "all_bundles":
            color = line_colors(sls)
        for sl in sls:
            if flip_axes[0]:
                sl[:, 0] = dimensions[0] - sl[:, 0]
            if flip_axes[1]:
                sl[:, 1] = dimensions[1] - sl[:, 1]
            if flip_axes[2]:
                sl[:, 2] = dimensions[2] - sl[:, 2]

        if color_by_direction:
            sl_actor = actor.line(sls, opacity=opacity)
        else:
            sl_actor = actor.line(sls, color, opacity=opacity)
        figure.add(sl_actor)
        sl_actor.GetProperty().SetRenderLinesAsTubes(1)
        sl_actor.GetProperty().SetLineWidth(6)

    return _inline_interact(figure, inline, interact)


def scene_rotate_forward(scene):
    scene.elevation(90)
    scene.set_camera(view_up=(0.0, 0.0, 1.0))
    scene.reset_camera()
    return scene


def create_gif(figure,
               file_name,
               n_frames=60,
               zoom=1,
               z_offset=0.5,
               size=(600, 600),
               rotate_forward=True):
    """
    Convert a Fury Scene object into a gif

    Parameters
    ----------
    figure: Fury Scene object
        Scene to be converted to a gif

    file_name: str
        File to save gif to.

    n_frames: int, optional
        Number of frames in gif.
        Will be evenly distributed throughout the rotation.
        Default: 60

    zoom: int, optional
        How much to magnify the figure in the fig.
        Default: 1

    size: tuple, optional
        Size of the gif.
        Default: (600, 600)

    rotate_forward: bool, optional
        Whether to rotate the figure forward before converting to a gif.
        Generally necessary for fury scenes.
        Default: True
    """
    if rotate_forward:
        figure = scene_rotate_forward(figure)

    tdir = tempfile.gettempdir()
    window.record(figure, az_ang=360.0 / n_frames, n_frames=n_frames,
                  path_numbering=True, out_path=tdir + '/tgif',
                  magnification=zoom,
                  size=size)

    vut.gif_from_pngs(tdir, file_name, n_frames,
                      png_fname="tgif", add_zeros=True)


def visualize_roi(roi, affine_or_mapping=None, static_img=None,
                  roi_affine=None, static_affine=None, reg_template=None,
                  name='ROI', figure=None, color=np.array([1, 0, 0]),
                  flip_axes=None,
                  opacity=1.0, inline=False, interact=False):
    """
    Render a region of interest into a VTK viz as a volume

    Parameters
    ----------
    roi : str or Nifti1Image
        The ROI information

    affine_or_mapping : ndarray, Nifti1Image, or str, optional
       An affine transformation or mapping to apply to the ROIs before
       visualization. Default: no transform.

    static_img: str or Nifti1Image, optional
        Template to resample roi to.
        Default: None

    roi_affine: ndarray, optional
        Default: None

    static_affine: ndarray, optional
        Default: None

    reg_template: str or Nifti1Image, optional
        Template to use for registration.
        Default: None

    name: str, optional
        Name of ROI for the legend.
        Default: 'ROI'

    color : ndarray, optional
        RGB color for ROI.
        Default: np.array([1, 0, 0])

    flip_axes : None
        This parameter is to conform fury and plotly APIs.

    opacity : float, optional
        Opacity of ROI.
        Default: 1.0

    figure : fury Scene object, optional
        If provided, the visualization will be added to this Scene. Default:
        Initialize a new Scene.

    interact : bool
        Whether to provide an interactive VTK window for interaction.
        Default: False

    inline : bool
        Whether to embed the visualization inline in a notebook. Only works
        in the notebook context. Default: False.

    Returns
    -------
    Fury Scene object
    """
    roi = vut.prepare_roi(roi, affine_or_mapping, static_img,
                          roi_affine, static_affine, reg_template)
    for i, flip in enumerate(flip_axes):
        if flip:
            roi = np.flip(roi, axis=i)
    if figure is None:
        figure = window.Scene()

    roi_actor = actor.contour_from_roi(roi, color=color, opacity=opacity)
    figure.add(roi_actor)

    return _inline_interact(figure, inline, interact)


def visualize_volume(volume, x=None, y=None, z=None, figure=None,
                     flip_axes=None,
                     opacity=0.6, inline=True, interact=False):
    """
    Visualize a volume

    Parameters
    ----------
    volume : ndarray or str
        3d volume to visualize.

    figure : fury Scene object, optional
        If provided, the visualization will be added to this Scene. Default:
        Initialize a new Scene.

    flip_axes : None
        This parameter is to conform fury and plotly APIs.

    opacity : float, optional
        Initial opacity of slices.
        Default: 0.6

    interact : bool
        Whether to provide an interactive VTK window for interaction.
        Default: False

    inline : bool
        Whether to embed the visualization inline in a notebook. Only works
        in the notebook context. Default: False.

    Returns
    -------
    Fury Scene object
    """
    volume = vut.load_volume(volume)

    if figure is None:
        figure = window.Scene()

    shape = volume.shape
    image_actor_z = actor.slicer(volume)
    slicer_opacity = opacity
    image_actor_z.opacity(slicer_opacity)

    image_actor_x = image_actor_z.copy()
    if x is None:
        x = int(np.round(shape[0] / 2))
    image_actor_x.display_extent(x,
                                 x,
                                 0,
                                 shape[1] - 1,
                                 0,
                                 shape[2] - 1)

    image_actor_y = image_actor_z.copy()

    if y is None:
        y = int(np.round(shape[1] / 2))
    image_actor_y.display_extent(0,
                                 shape[0] - 1,
                                 y,
                                 y,
                                 0,
                                 shape[2] - 1)

    figure.add(image_actor_z)
    figure.add(image_actor_x)
    figure.add(image_actor_y)

    show_m = window.ShowManager(figure, size=(1200, 900))
    show_m.initialize()

    if interact:
        line_slider_z = ui.LineSlider2D(min_value=0,
                                        max_value=shape[2] - 1,
                                        initial_value=shape[2] / 2,
                                        text_template="{value:.0f}",
                                        length=140)

        line_slider_x = ui.LineSlider2D(min_value=0,
                                        max_value=shape[0] - 1,
                                        initial_value=shape[0] / 2,
                                        text_template="{value:.0f}",
                                        length=140)

        line_slider_y = ui.LineSlider2D(min_value=0,
                                        max_value=shape[1] - 1,
                                        initial_value=shape[1] / 2,
                                        text_template="{value:.0f}",
                                        length=140)

        opacity_slider = ui.LineSlider2D(min_value=0.0,
                                         max_value=1.0,
                                         initial_value=slicer_opacity,
                                         length=140)

        def change_slice_z(slider):
            z = int(np.round(slider.value))
            image_actor_z.display_extent(
                0, shape[0] - 1, 0, shape[1] - 1, z, z)

        def change_slice_x(slider):
            x = int(np.round(slider.value))
            image_actor_x.display_extent(
                x, x, 0, shape[1] - 1, 0, shape[2] - 1)

        def change_slice_y(slider):
            y = int(np.round(slider.value))
            image_actor_y.display_extent(
                0, shape[0] - 1, y, y, 0, shape[2] - 1)

        def change_opacity(slider):
            slicer_opacity = slider.value
            image_actor_z.opacity(slicer_opacity)
            image_actor_x.opacity(slicer_opacity)
            image_actor_y.opacity(slicer_opacity)

        line_slider_z.on_change = change_slice_z
        line_slider_x.on_change = change_slice_x
        line_slider_y.on_change = change_slice_y
        opacity_slider.on_change = change_opacity

        def build_label(text):
            label = ui.TextBlock2D()
            label.message = text
            label.font_size = 18
            label.font_family = 'Arial'
            label.justification = 'left'
            label.bold = False
            label.italic = False
            label.shadow = False
            label.background = (0, 0, 0)
            label.color = (1, 1, 1)

            return label

        line_slider_label_z = build_label(text="Z Slice")
        line_slider_label_x = build_label(text="X Slice")
        line_slider_label_y = build_label(text="Y Slice")
        opacity_slider_label = build_label(text="Opacity")

        panel = ui.Panel2D(size=(300, 200),
                           color=(1, 1, 1),
                           opacity=0.1,
                           align="right")
        panel.center = (1030, 120)

        panel.add_element(line_slider_label_x, (0.1, 0.75))
        panel.add_element(line_slider_x, (0.38, 0.75))
        panel.add_element(line_slider_label_y, (0.1, 0.55))
        panel.add_element(line_slider_y, (0.38, 0.55))
        panel.add_element(line_slider_label_z, (0.1, 0.35))
        panel.add_element(line_slider_z, (0.38, 0.35))
        panel.add_element(opacity_slider_label, (0.1, 0.15))
        panel.add_element(opacity_slider, (0.38, 0.15))

        show_m.scene.add(panel)

        global size
        size = figure.GetSize()

        def win_callback(obj, event):
            global size
            if size != obj.GetSize():
                size_old = size
                size = obj.GetSize()
                size_change = [size[0] - size_old[0], 0]
                panel.re_align(size_change)

    show_m.initialize()

    figure.zoom(1.5)
    figure.reset_clipping_range()

    if interact:
        show_m.add_window_callback(win_callback)
        show_m.render()
        show_m.start()

    return _inline_interact(figure, inline, interact)


def _draw_core(sls, n_points, figure, bundle_name, indiv_profile,
               labelled_points, dimensions, flip_axes):
    fgarray = np.asarray(set_number_of_points(sls, n_points))
    fgarray = np.median(fgarray, axis=0)

    colormap = np.asarray([
        [0.265625, 0.00390625, 0.328125],
        [0.28125, 0.15625, 0.46875],
        [0.2421875, 0.28515625, 0.53515625],
        [0.19140625, 0.40625, 0.5546875],
        [0.1484375, 0.5078125, 0.5546875],
        [0.12109375, 0.6171875, 0.53515625],
        [0.20703125, 0.71484375, 0.47265625],
        [0.4296875, 0.8046875, 0.34375],
        [0.70703125, 0.8671875, 0.16796875],
        [0.98828125, 0.90234375, 0.14453125]])
    xp = np.linspace(
        np.min(indiv_profile),
        np.max(indiv_profile),
        num=len(colormap))
    line_color = np.ones((n_points, 3))
    for i in range(3):
        line_color[:, i] = np.interp(indiv_profile, xp, colormap[:, i])
    line_color_untouched = line_color.copy()
    for i in range(n_points):
        if i < n_points - 1:
            direc = fgarray[i + 1] - fgarray[i]
            direc = direc / np.linalg.norm(direc)
            light_direc = -fgarray[i] / np.linalg.norm(fgarray[i])
            direc_adjust = np.dot(direc, light_direc)
            direc_adjust = (direc_adjust + 3) / 4
        line_color[i, 0:3] = line_color[i, 0:3] * direc_adjust
    text = [None] * n_points
    for label in labelled_points:
        if label == -1:
            text[label] = str(n_points)
        else:
            text[label] = str(label)

    if flip_axes[0]:
        fgarray[:, 0] = dimensions[0] - fgarray[:, 0]
    if flip_axes[1]:
        fgarray[:, 1] = dimensions[1] - fgarray[:, 1]
    if flip_axes[2]:
        fgarray[:, 2] = dimensions[2] - fgarray[:, 2]

    sl_actor = actor.line([fgarray], line_color)
    figure.add(sl_actor)
    sl_actor.GetProperty().SetRenderLinesAsTubes(1)
    sl_actor.GetProperty().SetLineWidth(20)

    return line_color_untouched


def single_bundle_viz(indiv_profile, sft,
                      bundle, scalar_name,
                      bundle_dict=None,
                      flip_axes=[False, False, False],
                      labelled_nodes=[0, -1],
                      figure=None,
                      include_profile=False):
    """
    Visualize a single bundle in 3D with core bundle and associated profile

    Parameters
    ----------
    indiv_profile : ndarray
        A numpy array containing a tract profile for this bundle for a scalar.

    sft : Stateful Tractogram, str
        A Stateful Tractogram containing streamline information.
        If bundle is an int, the Stateful Tractogram
        must contain a bundle key in it's data_per_streamline which is a list
        of bundle `'uid'.
        Otherwise, the entire Stateful Tractogram will be used as the bundle
        for the visualization.

    bundle : str or int
        The name of the bundle to be used as the label for the plot,
        and for selection from the sft metadata.

    scalar_name : str
        The name of the scalar being used.

    bundle_dict : dict, optional
        This parameter is used if bundle is an int.
        Keys are names of bundles and values are dicts that specify them.
        Default: Either the entire sft is treated as a bundle,
        or identified only as unique integers in the metadata.

    flip_axes : ndarray
        Which axes to flip, to orient the image as RAS, which is how we
        visualize.
        For example, if the input image is LAS, use [True, False, False].
        Default: [False, False, False]

    labelled_nodes : list or ndarray
        Which nodes to label. -1 indicates the last node.
        Default: [0, -1]

    figure : Plotly Figure object, optional
        If provided, the visualization will be added to this Figure. Default:
        Initialize a new Figure.

    include_profile : bool, optional
        Not yet implemented in fury. Default: False

    Returns
    -------
    Fury Figure object
    """
    if figure is None:
        figure = window.Scene()
        figure.SetBackground(1, 1, 1)

    n_points = len(indiv_profile)
    sls, _, bundle_name, dimensions = next(vut.tract_generator(
        sft, bundle, bundle_dict, None, n_points))

    _draw_core(
        sls, n_points, figure, bundle_name, indiv_profile,
        labelled_nodes, dimensions, flip_axes)

    return figure
