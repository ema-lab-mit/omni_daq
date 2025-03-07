﻿// collinear_daq_driver_wrap.cpp : Defines the entry point for the console application.

#include "stdafx.h"
#include <pybind11/pybind11.h>
#include "timetagger4_interface.h"
#include <cstdio>
#include <iostream>
#include <vector>
#include <pybind11/stl.h>

using namespace std;

typedef unsigned int uint32;
typedef unsigned __int64 uint64;

class time_tagger_wrapper
{
public:
	// prepare configuration
	timetagger4_configuration config;
	timetagger4_device * device;
	timetagger4_read_in read_config;
	// structure with packet pointers for read data
	timetagger4_read_out read_data;

	int status;
	int channel_index;
	int packet_number;
	int error_code;
	const char * err_message;
	__int64 t0 = 0;

	// prepare initialization
	timetagger4_init_parameters params;

	// Constructor ("init")
	time_tagger_wrapper(
		bool channel_0_used = false,
		bool channel_1_used = false,
		bool channel_2_used = false,
		bool channel_3_used = false,
		bool trigger_rising = false,
		bool channel_0_rising = false,
		bool channel_1_rising = false,
		bool channel_2_rising = false,
		bool channel_3_rising = false,
		double trigger_level = -0.1,
		double channel_0_level = -0.1,
		double channel_1_level = -0.1,
		double channel_2_level = -0.1,
		double channel_3_level = -0.1,
		int channel_0_start = 0,
		int channel_1_start = 0,
		int channel_2_start = 0,
		int channel_3_start = 0,
		int channel_0_stop = 16000000,
		int channel_1_stop = 16000000,
		int channel_2_stop = 16000000,
		int channel_3_stop = 16000000,
		int index = 0
	)
	{
		timetagger4_get_default_init_parameters(&params);
		params.buffer_size[0] = 8 * 1024 * 1024;    // use 8 MByte as packet buffer
		params.board_id = index;                        // value copied to "card" field of every packet, allowed range 0..255
		params.card_index = index;                      // initialize first TimeTagger4 board found in the system
		channel_index = index;
													// initialize card
		device = timetagger4_init(&params, &error_code, &err_message);
		// printf("Device pointer after initializiation: %p\n", device);

		if (error_code != CRONO_OK)
		{
			cout << "Could not init TimeTagger4 compatible board: " << err_message << "\n";
		}
		// fill configuration data structure with default values
		// so that the configuration is valid and only parameters
		// of interest have to be set explicitly
		//timetagger4_get_default_configuration(device, &config);
		timetagger4_static_info static_info;
		timetagger4_get_static_info(device, &static_info);
		timetagger4_configuration config;
		timetagger4_get_default_configuration(device, &config);

		// printf("Device pointer after default config: %p\n", device);
		// start group on falling edges on the start channel
		if (trigger_rising == true)
		{
			config.trigger[0].falling = 0;
			config.trigger[0].rising = 1;
		}
		else {
			config.trigger[0].falling = 1;
			config.trigger[0].rising = 0;
		}

		config.dc_offset[0] = trigger_level;

		// set config of the 4 TDC channels
		if (channel_0_used == true) {
			// enable recording hits on channel
			config.channel[0].enabled = true;
			// define range of the group
			config.channel[0].start = channel_0_start;
			config.channel[0].stop = channel_0_stop;
			config.dc_offset[1] = channel_0_level;
			if (channel_0_rising == true)
			{
				config.trigger[1].falling = 0;
				config.trigger[1].rising = 1;
			}
			else {
				config.trigger[1].falling = 1;
				config.trigger[1].rising = 0;
			}

		}
		else
		{
			config.channel[0].enabled = false;
		}
		if (channel_1_used == true) {
			// enable recording hits on channel
			config.channel[1].enabled = true;
			// define range of the group
			config.channel[1].start = channel_1_start;
			config.channel[1].stop = channel_1_stop;
			config.dc_offset[2] = channel_1_level;
			if (channel_1_rising == true)
			{
				config.trigger[2].falling = 0;
				config.trigger[2].rising = 1;
			}
			else {
				config.trigger[2].falling = 1;
				config.trigger[2].rising = 0;
			}

		}
		else
		{
			config.channel[1].enabled = false;
		}
		if (channel_2_used == true) {
			// enable recording hits on channel
			config.channel[2].enabled = true;
			// define range of the group
			config.channel[2].start = channel_2_start;
			config.channel[2].stop = channel_2_stop;
			config.dc_offset[3] = channel_2_level;
			if (channel_1_rising == true)
			{
				config.trigger[3].falling = 0;
				config.trigger[3].rising = 1;
			}
			else {
				config.trigger[3].falling = 1;
				config.trigger[3].rising = 0;
			}

		}
		else
		{
			config.channel[2].enabled = false;
		}
		if (channel_3_used == true) {
			// enable recording hits on channel
			config.channel[3].enabled = true;
			// define range of the group
			config.channel[3].start = channel_3_start;
			config.channel[3].stop = channel_3_stop;
			config.dc_offset[4] = channel_3_level;
			if (channel_1_rising == true)
			{
				config.trigger[4].falling = 0;
				config.trigger[4].rising = 1;
			}
			else {
				config.trigger[4].falling = 1;
				config.trigger[4].rising = 0;
			}

		}
		else
		{
			config.channel[3].enabled = false;
		}

		// printf("--------------------------------!!!\n");
		// printf("dev before writing config: %p\n", device);
		// printf("--------------------------------!!!\n");
		// write configuration to board
		int status = timetagger4_configure(device, &config);
		// printf("dev after writing config: %p\n", device);
		// printf("--------------------------------!!!\n");

		// automatically acknowledge all data as processed
		// on the next call to timetagger4_read()
		// old packet pointers are invalid after calling timetagger4_read()
		read_config.acknowledge_last_read = 1;

		packet_number = 1;

	}

	int startReading()
	{
		// start data capture
		// printf("Before starting timetagger4_start_capture", device);
		status = timetagger4_start_capture(device);

		// printf("######################################"); //
		// printf("After starting timetagger4_start_capture", device);

		// printf("Started data capture on start reading");
		// printf("--------------------------------"); //
		// printf("Local status: %d\n", status);
		if (status != CRONO_OK) {
			printf("CRONO NOT OK\n");
			printf("Could not start capturing %s", timetagger4_get_last_error_message(device));
			timetagger4_close(device);
			return status;
		}
		// printf("Shoot reading failed, exit", timetagger4_get_last_error_message(device));
		return 0;
	}

	std::tuple<int, std::vector<std::array<int, 4>>> getPackets()
	{
		// expandable array we will put the packet data in
		std::vector<std::array<int, 4>> all_data;
		
		// get pointers to acquired packets
		status = timetagger4_read(device, &read_config, &read_data);
		if (status == CRONO_OK)
		{
			crono_packet* p = read_data.first_packet;
			while (p <= read_data.last_packet)
			{
				int hit_count = 2 * (p->length);
				if ((p->flags & 0x1) == 1)
					hit_count -= 1;

				uint32* packet_data = (uint32*)(p->data);
				int events = 0;
				for (int i = 0; i < hit_count; i++)
				{
					uint32* hit = (packet_data + i);
					// extract channel number
					int channel = (*hit & 0xf);

					if (channel < 4) {
						events = events + 1;
					}
				}
				if(events == 0){
					all_data.push_back({ packet_number,0,-1,-1});
				}
				else{
					for (int i = 0; i < hit_count; i++)
					{
						uint32* hit = (packet_data + i);
						// extract channel number
						int channel = (*hit & 0xf);

						// extract hit timestamp
						int ts_offset = (*hit >> 8 & 0xffffff);
						if (channel < 4) {
							all_data.push_back({ packet_number,events,channel + channel_index*4,ts_offset });
						}
					}
				}
				// go to next packet
				p = crono_next_packet(p);
				packet_number = packet_number + 1;
			}

		}
		return std::make_tuple(status, all_data);
	}

	int stopReading()
	{
		// shut down packet generation and DMA transfers
		timetagger4_stop_capture(device);
		return 0;
	}

	int stop()
	{
		// deactivate timetagger4
		timetagger4_close(device);
		return 0;
	}


};

namespace py = pybind11;

PYBIND11_MODULE(timetagger4, m) {
	py::class_<time_tagger_wrapper>(m, "TimeTagger")
		.def(py::init<bool, bool, bool, bool, bool, bool, bool, bool, bool,
			double, double, double, double, double,
			int, int, int, int, int, int, int, int, int>(),
			py::arg("channel_0_used") = false,
			py::arg("channel_1_used") = false,
			py::arg("channel_2_used") = false,
			py::arg("channel_3_used") = false,
			py::arg("trigger_rising") = false,
			py::arg("channel_0_rising") = false,
			py::arg("channel_1_rising") = false,
			py::arg("channel_2_rising") = false,
			py::arg("channel_3_rising") = false,
			py::arg("trigger_level") = -0.1,
			py::arg("channel_0_level") = -0.1,
			py::arg("channel_1_level") = -0.1,
			py::arg("channel_2_level") = -0.1,
			py::arg("channel_3_level") = -0.1,
			py::arg("channel_0_start") = 0,
			py::arg("channel_1_start") = 0,
			py::arg("channel_2_start") = 0,
			py::arg("channel_3_start") = 0,
			py::arg("channel_0_stop") = 16000000,
			py::arg("channel_1_stop") = 16000000,
			py::arg("channel_2_stop") = 16000000,
			py::arg("channel_3_stop") = 16000000,
			py::arg("index") = 0)
		.def("startReading", &time_tagger_wrapper::startReading)
		.def("getPackets", &time_tagger_wrapper::getPackets)
		.def("stopReading", &time_tagger_wrapper::stopReading)
		.def("stop", &time_tagger_wrapper::stop)
		;
}

