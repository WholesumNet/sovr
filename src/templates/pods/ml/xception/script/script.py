#!/usr/bin/env python3
from datetime import datetime, timedelta
import pathlib
import sys
import base64
import glob

from yapapi import (
    Golem,
    Task,
    WorkContext,
)
from yapapi.payload import vm
from yapapi.rest.activity import BatchTimeoutError

utils_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(utils_dir))

from utils import (
    build_parser,
    TEXT_COLOR_CYAN,
    TEXT_COLOR_DEFAULT,
    TEXT_COLOR_RED,
    TEXT_COLOR_MAGENTA,
    format_usage,
    run_golem_example,
    print_env_info,
)

# Keras applications pretrained models' images
AvailableModels = {
  'densenet121': {
    'image_hash': 'caeb6ef9dc9a682dd50b62b7781fb3fbcc7c6e26e53c52835fb8b287',
    'classifier': 'densenet',
  },
  'densenet169': {
    'image_hash': 'caeb6ef9dc9a682dd50b62b7781fb3fbcc7c6e26e53c52835fb8b287',
    'classifier': 'densenet',
  },
  'densenet201': {
    'image_hash': 'caeb6ef9dc9a682dd50b62b7781fb3fbcc7c6e26e53c52835fb8b287',
    'classifier': 'densenet',
  },
  'nasnet_large': {
    'image_hash': 'd4ecd446b169934ac08e74e6ac04a8e92f1ed6817664bf2b46dfbed3',
    'classifier': 'nasnet',
  },
  'nasnet_mobile': {
    'image_hash': 'd4ecd446b169934ac08e74e6ac04a8e92f1ed6817664bf2b46dfbed3',
    'classifier': 'nasnet',
  },
  'resnet50': {
    'image_hash': '870e2fb0f95a6d6152c97d3fe02400aac88f98a8dc523a2ac8cf42b2',
    'classifier': 'resnet'
  },
  'resnet101': {
    'image_hash': '870e2fb0f95a6d6152c97d3fe02400aac88f98a8dc523a2ac8cf42b2',
    'classifier': 'resnet'
  },
  'resnet152': {
    'image_hash': '870e2fb0f95a6d6152c97d3fe02400aac88f98a8dc523a2ac8cf42b2',
    'classifier': 'resnet'
  },
  'resnet50v2': {
    'image_hash': '870e2fb0f95a6d6152c97d3fe02400aac88f98a8dc523a2ac8cf42b2',
    'classifier': 'resnet'
  },
  'resnet101v2': {
    'image_hash': '870e2fb0f95a6d6152c97d3fe02400aac88f98a8dc523a2ac8cf42b2',
    'classifier': 'resnet'
  },
  'resnet152v2': {
    'image_hash': '870e2fb0f95a6d6152c97d3fe02400aac88f98a8dc523a2ac8cf42b2',
    'classifier': 'resnet'
  },
  'vgg16': {
    'image_hash': '360898f1a2e7d0962bce2ca62e1ab0e39e89f27f0ccf75d66b8cef4a',
    'classifier': 'vgg'
  },
  'vgg19': {
    'image_hash': '360898f1a2e7d0962bce2ca62e1ab0e39e89f27f0ccf75d66b8cef4a',
    'classifier': 'vgg'
  },
  'xception': {
    'image_hash': '31cac0ac35b468c77654dc35a9cc0f0afb15ad4e188f7dbdbb96a5bc',
    'classifier': 'inception_v3.xception'
  },
  'inception_v3': {
    'image_hash': '31cac0ac35b468c77654dc35a9cc0f0afb15ad4e188f7dbdbb96a5bc',
    'classifier': 'inception_v3.xception'
  },
  'inception_resnet_v2': {
    'image_hash': '000e381cc34a16f3f59cd4fccc9e501a91804987e006353f2d489d66',
    'classifier': 'inception_resnet_v2'
  },
}


async def main(
    model, images, subnet_tag, min_cpu_threads, payment_driver=None, payment_network=None, show_usage=False
):
    package = await vm.repo(
        image_hash=AvailableModels[model]['image_hash'],
        # only run on provider nodes that have more than 0.5gb of RAM available
        min_mem_gib=3.0,
        # only run on provider nodes that have more than 2gb of storage space available
        min_storage_gib=4.0,
        # only run on provider nodes which a certain number of CPU threads (logical CPU cores) available
        min_cpu_threads=min_cpu_threads,
    )
    classifier = AvailableModels[model]['classifier']
    async def worker(ctx: WorkContext, tasks):
        script_dir = pathlib.Path(__file__).resolve().parent.parent               
        # Set timeout for the first script executed on the provider. Usually, 30 seconds
        # should be more than enough for computing a single frame of the provided scene,
        # however a provider may require more time for the first task if it needs to download
        # the VM image first. Once downloaded, the VM image will be cached and other tasks that use
        # that image will be computed faster.
        script = ctx.new_script(timeout=timedelta(minutes=1))

        async for task in tasks:
            params = {
                "model": model,
                "reqs": [                    
                    {
                        "id": index,
                        "image": image,
                    } for index, image in enumerate(images)
                ],
            }

            script.upload_json(
                params,
                "/golem/work/params.json",
            )
            script.upload_file(
                f'{script_dir}/script/classifiers/{classifier}.py',
                '/golem/work/classify.py'
            ) 
            commands = (
                'python3 /golem/work/classify.py > /golem/output/log 2>&1;'
            )
            script.run('/bin/sh',
                '-c',
                commands    
            )
            output_file = f"{script_dir}/output/preds.json"
            script.download_file(f"/golem/output/preds.json", output_file)
            script.download_file(f"/golem/output/log", f'{script_dir}/logs/log')
            try:
                yield script
                # TODO: Check if job results are valid
                # and reject by: task.reject_task(reason = 'invalid file')
                task.accept_result(result=output_file)
            except BatchTimeoutError:
                print(
                    f"{TEXT_COLOR_RED}"
                    f"Task {task} timed out on {ctx.provider_name}, time: {task.running_time}"
                    f"{TEXT_COLOR_DEFAULT}"
                )
                raise

            # reinitialize the script which we send to the engine to compute subsequent frames
            script = ctx.new_script(timeout=timedelta(minutes=1))

            if show_usage:
                raw_state = await ctx.get_raw_state()
                usage = format_usage(await ctx.get_usage())
                cost = await ctx.get_cost()
                print(
                    f"{TEXT_COLOR_MAGENTA}"
                    f" --- {ctx.provider_name} STATE: {raw_state}\n"
                    f" --- {ctx.provider_name} USAGE: {usage}\n"
                    f" --- {ctx.provider_name}  COST: {cost}"
                    f"{TEXT_COLOR_DEFAULT}"
                )

    
    # Worst-case overhead, in minutes, for initialization (negotiation, file transfer etc.)
    # TODO: make this dynamic, e.g. depending on the size of files to transfer
    init_overhead = 3
    # Providers will not accept work if the timeout is outside of the [5 min, 30min] range.
    # We increase the lower bound to 6 min to account for the time needed for our demand to
    # reach the providers.
    min_timeout, max_timeout = 6, 30

    timeout = timedelta(minutes=max(min(init_overhead, max_timeout), min_timeout))

    async with Golem(
        budget=1.0,
        subnet_tag=subnet_tag,
        payment_driver=payment_driver,
        payment_network=payment_network,
    ) as golem:
        print_env_info(golem)

        num_tasks = 0
        start_time = datetime.now()

        completed_tasks = golem.execute_tasks(
            worker,
            [Task(data={})],
            payload=package,
            max_workers=3,
            timeout=timeout,
        )
        async for task in completed_tasks:
            num_tasks += 1
            print(
                f"{TEXT_COLOR_CYAN}"
                f"Task computed: {task}, result: {task.result}, time: {task.running_time}"
                f"{TEXT_COLOR_DEFAULT}"
            )

        print(
            f"{TEXT_COLOR_CYAN}"
            f"{num_tasks} tasks computed, total time: {datetime.now() - start_time}"
            f"{TEXT_COLOR_DEFAULT}"
        )


if __name__ == "__main__":
    parser = build_parser("Classify images using Keras applications")
    parser.add_argument("--model", help="specify the model, e.g. densenet121")
    parser.add_argument("--images", help="input images directory path")
    parser.add_argument("--show-usage", action="store_true", help="show activity usage and cost")
    parser.add_argument(
        "--min-cpu-threads",
        type=int,
        default=1,
        help="require the provider nodes to have at least this number of available CPU threads",
    )
    now = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
    script_dir = pathlib.Path(__file__).resolve().parent.parent
    parser.set_defaults(log_file=f"{script_dir}/logs/{now}")
    args = parser.parse_args()

    images = []
    for filename in glob.iglob(f'{args.images}/*.jpg'):
        with open(filename, 'rb') as f:
            images.append(base64.b64encode(f.read()).decode('utf-8'))

    run_golem_example(
        main(
            model=args.model,
            images=images,
            subnet_tag=args.subnet_tag,
            min_cpu_threads=args.min_cpu_threads,
            payment_driver=args.payment_driver,
            payment_network=args.payment_network,
            show_usage=args.show_usage,
        ),
        log_file=args.log_file,
    )
