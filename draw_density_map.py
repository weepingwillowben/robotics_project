from html.parser import HTMLParser
import pygame
import argparse
import json
import time
import os
import shutil
import subprocess
from visibility import LibVisibility
#from parse_svg import SimpleSVGParser
import coord_math
from enviornment import EnviornmentCoordinator
from follow_path_strategy import Follower
from static_pathing import dikstras
from struct_ import Struct
from gtsp import GTSP,get_path
import numpy as np
import random

def renderPolys(screen,polys):
    black = (0,0,0)
    for poly in polys:
        #print(x1,y1)
        pygame.draw.polygon(screen,black,poly,3)

def renderRewards(screen,rewards):
    for rx,ry in rewards:
        irew = (int(rx),int(ry))
        pygame.draw.circle(screen, (255, 0, 0), irew, 5)

def negative_circle(cen,map_info,radius):
    poly = []
    poly.append((map_info.width-1,0))
    for point in coord_math.get_rays(cen,29,radius):
        poly.append(point)
    poly.append(coord_math.add((radius,0),cen))
    poly.append((map_info.width-1,0))
    poly.append((map_info.width-1,map_info.height-1))
    poly.append((0,map_info.height-1))
    poly.append((0,0))
    return poly

def renderSight(screen,map_info,poly,cen,radius,color):
    poly_screen = pygame.Surface((map_info.width, map_info.height), pygame.SRCALPHA)  # the size of your rect
    #poly_screen.set_alpha(128)

    if poly:
        pygame.draw.polygon(poly_screen,color,poly)

    #pygame.draw.circle(poly_screen, color, cen, radius)

    blank = (0,0,0,0)
    #if poly:
        #pygame.draw.polygon(screen,color,poly,3)
    #    pygame.draw.polygon(poly_screen,blank,poly)
    neg_circle = negative_circle(cen,map_info,radius)
    pygame.draw.polygon(poly_screen,blank,neg_circle)
    #pygame.draw.circle(poly_screen,blank, cen, radius)

    screen.blit(poly_screen, (0,0))


def save_video(img_dir,out_name):
    ffmpeg_call = [
        "ffmpeg",
        "-y",# overwrite output.mp4 if already there
        "-hide_banner","-loglevel","error", #don't print out unnecessary stuff
        "-pattern_type", "glob","-i","{}data*.png".format(img_dir),# get input from image list
        "-c:v","libx264",#deine output format
        "-r","30", #define output sample rate
        "-pix_fmt","yuv420p",#???
        out_name
    ]
    subprocess.call(ffmpeg_call)
    shutil.rmtree(img_dir)

def draw_density_map(screen,libvis,map_info,weightmap,pointlist,index,color,radius):
    #accel_surface = pygame.Surface((map_info.width, map_info.height),pygame.SRCALPHA)#,pygame.RLEACCEL)
    #screen.fill((255, 255, 255,0))
    for i in range(20):#len(weightmap)):
        point = pointlist[weightmap[i][index]]
        poly = libvis.get_visibilily_polygon(point)
        renderSight(screen,map_info,poly,point,radius,color)
    #screen.blit(accel_surface,(0,0))


def to_point_paths(visibilty_info,paths):
    plist = visibilty_info['points']
    return [[plist[p] for p in path] for path in paths]

def main():
    parser = argparse.ArgumentParser(description='run ai enviornmnent')
    parser.add_argument('json_fname', type=str, help='enviornment json file')
    parser.add_argument('-V', '--produce_video', action='store_true',help="produces video of screen")
    parser.add_argument('-D', '--no_display', action='store_true',help="disables drawing to screen")
    args = parser.parse_args()
    print(args.no_display)

    basename = os.path.basename(args.json_fname).split(".")[0]
    img_dir = basename+"_img_dir/"
    video_name = basename+"_vid.mp4"
    if os.path.exists(img_dir):
        shutil.rmtree(img_dir)
    if args.produce_video:
        os.makedirs(img_dir,exist_ok=True)

    #gtsp = GTSP()

    env_values = Struct(**json.load(open(args.json_fname)))

    visibilty_info = json.load(open(env_values.adjacency_list))

    map_info = Struct(**json.load(open(env_values.map_fname)))

    agent_weightmap = json.load(open(env_values.agent_weightmap))
    guard_weightmap = json.load(open(env_values.guard_weightmap))

    #agent_screen_out = renderPossiblePaths(map_info,to_point_paths(visibilty_info,agent_weightmap),(0,255,0,4))
    #guard_screen_out = renderPossiblePaths(map_info,to_point_paths(visibilty_info,guard_weightmap),(0,0,255,4))
    #print(map_info.blocker_polygons)
    #pygame.image.save(agent_screen_out,"guard_density_maps.png")
    #pygame.image.save(guard_screen_out,"agent_density_maps.png")

    libvis = LibVisibility(map_info.blocker_polygons,map_info.width,map_info.height)

    pygame.init()

    if not args.no_display:
        screen = pygame.display.set_mode([map_info.width, map_info.height])
    else:
        screen = pygame.Surface((map_info.width, map_info.height), pygame.SRCALPHA)

    running = True
    count = 1
    frame_count = 0
    while running:
        # Did the user click the window close button?
        if not args.no_display:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

        #enviornment.step_move()
        #if enviornment.game_finished():
        #    print("result: {}".format(enviornment.game_result()))
        #    running = False

        if frame_count > len(agent_weightmap[0]):
            running = False

        time.sleep(0.05)

        # Fill the background with white
        screen.fill((255, 255, 255))

        #screen.blit(guard_screen_out, (0,0))
        #screen.blit(agent_screen_out, (0,0))
        #tmpscreen = pygame.Surface((map_info.width, map_info.height), pygame.SRCALPHA)

        #tmpscreen.fill((0, 0, 0,0))
        draw_density_map(screen,libvis,map_info,guard_weightmap,visibilty_info['points'],frame_count,(0,255,0,16),env_values.guard_linesight)
        draw_density_map(screen,libvis,map_info,agent_weightmap,visibilty_info['points'],frame_count,(0,0,255,16),10)
        #screen.blit(tmpscreen,(0,0))

        renderPolys(screen,map_info.blocker_polygons)
        # Draw a solid blue circle in the center
        count += 1
        #poly = libvis.get_visibilily_polygon((count, count))
        #print(poly)
        #time.sleep(0.01)
        # counts = visibilty_info['counts']
        # avg_value = sum(counts,0)/len(counts)
        # for point,value in zip(visibilty_info['points'],visibilty_info['counts']):
        #     #print(value)
        #     pygame.draw.circle(screen, (0, 255, 0,128), point, int(value/(0.8*avg_value)))

        renderRewards(screen,map_info.reward_points)
        #renderSight(screen,map_info,poly)

        #path_targets = find_path_points(visibilty_info,gtsp,(count,count),map_info.reward_points)
        #renderPath(screen,path_points)

        #pygame.draw.line(screen, (0, 0, 255), (250, 250),  (250, 0),3)

        # Flip the display

        if not args.no_display:
            pygame.display.flip()
        SAMPLE_RATE = 1
        if args.produce_video and frame_count % SAMPLE_RATE == 0:
            pygame.image.save(screen, img_dir+"data{0:05d}.png".format(frame_count//SAMPLE_RATE))
        frame_count += 1


    if args.produce_video:
        save_video(img_dir,video_name)
    # Done! Time to quit.
    pygame.quit()

if __name__=="__main__":
    main()
