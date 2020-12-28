all: build run

# Define the GPIO pin numbers used by this hardware configuration

# GPIO numbers (LEDs, Relays, and Buttons)
MY_LED_COOL_0:=13
MY_LED_COOL_1:=19
MY_LED_COOL_2:=26
MY_RELAY_COOL:=14
MY_BUTTON_COOL_MORE:=9
MY_BUTTON_COOL_LESS:=11
MY_LED_WARM_0:=16
MY_LED_WARM_1:=20
MY_LED_WARM_2:=21
MY_RELAY_WARM:=15
MY_BUTTON_WARM_MORE:=25
MY_BUTTON_WARM_LESS:=8

build:
	docker build -t ibmosquito/tempctrl:1.0.0 .

# Running `make dev` will setup a working environment, just the way I like it.
# On entry to the container's bash shell, run `cd /outside/src` to work here.
dev: build
	-docker rm -f tempctrl 2> /dev/null || :
	docker run -it --name tempctrl \
            --privileged --restart unless-stopped \
            -e MY_LED_COOL_0=$(MY_LED_COOL_0) \
            -e MY_LED_COOL_1=$(MY_LED_COOL_1) \
            -e MY_LED_COOL_2=$(MY_LED_COOL_2) \
            -e MY_RELAY_COOL=$(MY_RELAY_COOL) \
            -e MY_BUTTON_COOL_MORE=$(MY_BUTTON_COOL_MORE) \
            -e MY_BUTTON_COOL_LESS=$(MY_BUTTON_COOL_LESS) \
            -e MY_LED_WARM_0=$(MY_LED_WARM_0) \
            -e MY_LED_WARM_1=$(MY_LED_WARM_1) \
            -e MY_LED_WARM_2=$(MY_LED_WARM_2) \
            -e MY_RELAY_WARM=$(MY_RELAY_WARM) \
            -e MY_BUTTON_WARM_MORE=$(MY_BUTTON_WARM_MORE) \
            -e MY_BUTTON_WARM_LESS=$(MY_BUTTON_WARM_LESS) \
            --volume `pwd`:/outside \
            ibmosquito/tempctrl:1.0.0 /bin/sh

# Run the container as a daemon (build not forecd here, sp must build it first)
run:
	-docker rm -f tempctrl 2> /dev/null || :
	docker run -d --name tempctrl \
            --privileged --restart unless-stopped \
            -e MY_LED_COOL_0=$(MY_LED_COOL_0) \
            -e MY_LED_COOL_1=$(MY_LED_COOL_1) \
            -e MY_LED_COOL_2=$(MY_LED_COOL_2) \
            -e MY_RELAY_COOL=$(MY_RELAY_COOL) \
            -e MY_BUTTON_COOL_MORE=$(MY_BUTTON_COOL_MORE) \
            -e MY_BUTTON_COOL_LESS=$(MY_BUTTON_COOL_LESS) \
            -e MY_LED_WARM_0=$(MY_LED_WARM_0) \
            -e MY_LED_WARM_1=$(MY_LED_WARM_1) \
            -e MY_LED_WARM_2=$(MY_LED_WARM_2) \
            -e MY_RELAY_WARM=$(MY_RELAY_WARM) \
            -e MY_BUTTON_WARM_MORE=$(MY_BUTTON_WARM_MORE) \
            -e MY_BUTTON_WARM_LESS=$(MY_BUTTON_WARM_LESS) \
            ibmosquito/tempctrl:1.0.0

exec:
	docker exec -it tempctrl /bin/sh

push:
	docker push ibmosquito/tempctrl:1.0.0

stop:
	-docker rm -f tempctrl 2>/dev/null || :

clean: stop
	-docker rmi ibmosquito/tempctrl:1.0.0 2>/dev/null || :

.PHONY: all build dev run push exec stop clean

